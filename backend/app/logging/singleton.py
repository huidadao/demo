"""Transaction logger singleton (Singleton Pattern)."""

import asyncio
from typing import Optional

from app.logging.models import LogEntry
from app.logging.formatters import LogFormatter, PlainTextFormatter
from app.logging.repositories import LogRepository, FileLogRepository


class TransactionLogger:
    """
    Singleton logger for API transaction logs.
    
    Singleton Pattern: Ensures only one logger instance exists
    across the application lifecycle, providing a global point
    of access to the logging subsystem.
    
    Usage:
        logger = TransactionLogger()
        await logger.log(entry)
    """

    _instance: Optional["TransactionLogger"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls) -> "TransactionLogger":
        """
        Override __new__ to enforce singleton behavior.
        
        Note: This is not thread-safe for instantiation across
        different event loops, but is safe within a single async app.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        repository: Optional[LogRepository] = None,
        formatter: Optional[LogFormatter] = None,
    ) -> None:
        """
        Initialize the singleton logger (only once).

        Args:
            repository: Concrete log repository. Defaults to FileLogRepository.
            formatter: Concrete log formatter. Defaults to PlainTextFormatter.
        """
        if self._initialized:
            return

        self._repository = repository or FileLogRepository()
        self._formatter = formatter or PlainTextFormatter()
        self._initialized = True

    async def log(self, entry: LogEntry) -> None:
        """
        Log a transaction entry asynchronously.

        Args:
            entry: The log entry to persist.
        """
        formatted = self._formatter.format(entry)
        await self._repository.save(formatted)

    async def close(self) -> None:
        """Clean up repository resources."""
        await self._repository.close()
