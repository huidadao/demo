"""Plain text formatter strategy (Concrete Strategy)."""

from app.logging.formatters.base import LogFormatter
from app.logging.models import LogEntry


class PlainTextFormatter(LogFormatter):
    """
    Formats log entries as human-readable plain text.
    
    Example:
        [2024-01-15T09:30:00Z] POST /auth/login | 200 | 45.2ms | IP: 192.168.1.1 | User: 5 | Body: {"email": "user@example.com"}
    """

    def format(self, entry: LogEntry) -> str:
        """
        Format a LogEntry as plain text.

        Args:
            entry: The log entry to format.

        Returns:
            Single-line formatted log string.
        """
        body_str = ""
        if entry.request_body is not None:
            body_items = []
            for key, value in entry.request_body.items():
                body_items.append(f"{key}={value}")
            body_str = " | Body: {" + ", ".join(body_items) + "}"

        user_str = f"User: {entry.user_id}" if entry.user_id else "User: anonymous"
        ua_str = f" | UA: {entry.user_agent}" if entry.user_agent else ""
        size_str = f" | Size: {entry.response_size}B" if entry.response_size else ""
        error_str = f" | ERROR: {entry.error_message}" if entry.error_message else ""

        return (
            f"[{entry.timestamp.isoformat()}] "
            f"{entry.method} {entry.path} | "
            f"Status: {entry.status_code} | "
            f"Duration: {entry.duration_ms:.2f}ms | "
            f"IP: {entry.client_ip} | "
            f"{user_str}"
            f"{body_str}"
            f"{ua_str}"
            f"{size_str}"
            f"{error_str}"
        )
