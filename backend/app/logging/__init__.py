"""Logging module with design patterns for transaction tracking.

Patterns Used:
- Singleton: TransactionLogger
- Repository: LogRepository / FileLogRepository
- Strategy: LogFormatter / PlainTextFormatter
- Builder: LogEntryBuilder
- Chain of Responsibility: TransactionLoggingMiddleware
"""

from .models import LogEntry
from .builders import LogEntryBuilder
from .singleton import TransactionLogger
from .middleware import TransactionLoggingMiddleware
from .repositories import LogRepository, FileLogRepository
from .formatters import LogFormatter, PlainTextFormatter

__all__ = [
    "LogEntry",
    "LogEntryBuilder",
    "TransactionLogger",
    "TransactionLoggingMiddleware",
    "LogRepository",
    "FileLogRepository",
    "LogFormatter",
    "PlainTextFormatter",
]
