"""Formatter strategy interface (Strategy Pattern)."""

from abc import ABC, abstractmethod

from app.logging.models import LogEntry


class LogFormatter(ABC):
    """
    Abstract base class for log formatters.
    
    Strategy Pattern: Allows swapping different formatting strategies
    (e.g., PlainText, JSON, CSV) without changing the logger code.
    """

    @abstractmethod
    def format(self, entry: LogEntry) -> str:
        """
        Format a LogEntry into a string representation.

        Args:
            entry: The log entry to format.

        Returns:
            Formatted string.
        """
        pass
