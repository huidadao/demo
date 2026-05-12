"""FastAPI middleware for request logging (Chain of Responsibility Pattern)."""

import time
import asyncio
from typing import Optional, Dict, Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.logging.singleton import TransactionLogger
from app.logging.builders import LogEntryBuilder
from app.logging.repositories import FileLogRepository
from app.logging.formatters import PlainTextFormatter


class TransactionLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts all HTTP requests and responses,
    builds a LogEntry, and asynchronously persists it.
    
    Chain of Responsibility Pattern: The middleware sits in the
    request/response processing chain, handling logging before
    passing control to the next handler.
    """

    # Fields to mask in request bodies (security)
    _SENSITIVE_FIELDS = {"password", "password_hash", "token", "access_token", "secret"}

    def __init__(self, app) -> None:
        """Initialize middleware and ensure singleton logger exists."""
        super().__init__(app)
        # Initialize singleton with default file repository and plain text formatter
        self._logger = TransactionLogger(
            repository=FileLogRepository(),
            formatter=PlainTextFormatter(),
        )

    @staticmethod
    def _mask_sensitive_data(body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive fields in request body.

        Args:
            body: Original request body dict.

        Returns:
            Body with sensitive values replaced.
        """
        if not isinstance(body, dict):
            return body
        masked = {}
        for key, value in body.items():
            if key.lower() in TransactionLoggingMiddleware._SENSITIVE_FIELDS:
                masked[key] = "****"
            else:
                masked[key] = value
        return masked

    @staticmethod
    async def _get_request_body(request: Request) -> Optional[Dict[str, Any]]:
        """
        Safely read and restore request body for logging.

        Args:
            request: FastAPI request object.

        Returns:
            Parsed JSON body dict or None.
        """
        try:
            body = await request.body()
            if not body:
                return None
            # Restore body so downstream can still read it
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

            import json
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    @staticmethod
    def _extract_user_id(request: Request) -> Optional[int]:
        """
        Extract user ID from request state if authentication middleware has run.

        Args:
            request: FastAPI request object.

        Returns:
            User ID or None.
        """
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return user.id
        return None

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request/response and log transaction asynchronously.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler in chain.

        Returns:
            Response from downstream handler.
        """
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent")

        # Read request body for logging (only for methods that typically have bodies)
        body_dict: Optional[Dict[str, Any]] = None
        if method in ("POST", "PUT", "PATCH"):
            body_dict = await self._get_request_body(request)
            if body_dict:
                body_dict = self._mask_sensitive_data(body_dict)

        # Execute the actual request handler
        error_message: Optional[str] = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            error_message = str(exc)
            raise exc
        finally:
            # Always calculate duration and log
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Extract response size if available
            response_size: Optional[int] = None
            if "response" in locals():
                try:
                    body_iterator = response.body_iterator
                    # For Starlette responses, try to get content length
                    if hasattr(response, "body"):
                        response_size = len(response.body)
                except Exception:
                    pass

            # Build log entry via Builder Pattern
            builder = LogEntryBuilder()
            entry = (
                builder
                .with_request_info(method, path)
                .with_response_info(status_code, duration_ms)
                .with_client_info(client_ip, user_agent)
                .with_user(self._extract_user_id(request))
                .with_body(body_dict)
                .with_response_size(response_size)
                .with_error(error_message)
                .build()
            )

            # Asynchronously log without blocking response
            asyncio.create_task(self._logger.log(entry))

        return response
