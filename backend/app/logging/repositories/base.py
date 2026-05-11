"""Repository pattern interface (Repository Pattern)."""

from abc import ABC, abstractmethod


class LogRepository(ABC):
    """
    Abstract base class for log storage repositories.
    
    Repository Pattern: Abstracts the storage mechanism so that
    the logger does not depend on concrete storage details.
    Swapping from file storage to database storage only requires
    implementing a new concrete repository.
    """

    @abstractmethod
    async def save(self, formatted_log: str) -> None:
        """
        Save a formatted log entry.

        Args:
            formatted_log: The log string to persist.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up any resources."""
        pass
