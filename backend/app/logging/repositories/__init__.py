"""Log repositories package."""

from .base import LogRepository
from .file_repository import FileLogRepository

__all__ = ["LogRepository", "FileLogRepository"]
