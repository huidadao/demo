"""Log entry builder (Builder Pattern)."""

from datetime import datetime
from typing import Optional, Dict, Any, Self

from app.logging.models import LogEntry


class LogEntryBuilder:
    """
    Builder for constructing LogEntry objects step-by-step.
    
    Builder Pattern: Separates the construction of a complex object
    from its representation, allowing the same construction process
    to create different representations.
    
    Example:
        entry = (
            LogEntryBuilder()
            .with_request_info("POST", "/auth/login")
            .with_response_info(200, 45.2)
            .with_client_info("192.168.1.1", "Mozilla/5.0")
            .with_user(5)
            .with_body({"email": "user@example.com"})
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize builder with default values."""
        self._timestamp: datetime = datetime.utcnow()
        self._method: str = ""
        self._path: str = ""
        self._status_code: int = 0
        self._duration_ms: float = 0.0
        self._client_ip: str = "unknown"
        self._user_agent: Optional[str] = None
        self._user_id: Optional[int] = None
        self._request_body: Optional[Dict[str, Any]] = None
        self._response_size: Optional[int] = None

    def with_timestamp(self, timestamp: datetime) -> Self:
        """Set the log timestamp."""
        self._timestamp = timestamp
        return self

    def with_request_info(self, method: str, path: str) -> Self:
        """Set HTTP method and path."""
        self._method = method
        self._path = path
        return self

    def with_response_info(self, status_code: int, duration_ms: float) -> Self:
        """Set response status code and processing duration."""
        self._status_code = status_code
        self._duration_ms = duration_ms
        return self

    def with_client_info(self, client_ip: str, user_agent: Optional[str] = None) -> Self:
        """Set client IP and user agent."""
        self._client_ip = client_ip
        self._user_agent = user_agent
        return self

    def with_user(self, user_id: Optional[int]) -> Self:
        """Set authenticated user ID."""
        self._user_id = user_id
        return self

    def with_body(self, body: Optional[Dict[str, Any]]) -> Self:
        """Set request body (sensitive fields are masked externally)."""
        self._request_body = body
        return self

    def with_response_size(self, size: Optional[int]) -> Self:
        """Set response body size in bytes."""
        self._response_size = size
        return self

    def build(self) -> LogEntry:
        """
        Build and return the LogEntry.

        Returns:
            Constructed LogEntry instance.
        """
        return LogEntry(
            timestamp=self._timestamp,
            method=self._method,
            path=self._path,
            status_code=self._status_code,
            duration_ms=self._duration_ms,
            client_ip=self._client_ip,
            user_agent=self._user_agent,
            user_id=self._user_id,
            request_body=self._request_body,
            response_size=self._response_size,
        )
