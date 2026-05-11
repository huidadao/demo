"""File-based log repository (Concrete Repository)."""

import os
import asyncio
from datetime import datetime
from pathlib import Path

from app.logging.repositories.base import LogRepository


class FileLogRepository(LogRepository):
    """
    Concrete repository that persists logs to rotating text files.
    
    Features:
    - Daily log rotation (transactions_YYYY-MM-DD.log)
    - 30-day retention
    - Async file I/O via thread pool
    - Automatic directory creation
    """

    def __init__(self, log_dir: str = "logs") -> None:
        """
        Initialize the file repository.

        Args:
            log_dir: Directory to store log files.
        """
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_log_file(self) -> Path:
        """
        Get the log file path for the current day.

        Returns:
            Path to today's log file.
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self._log_dir / f"transactions_{today}.log"

    def _cleanup_old_logs(self) -> None:
        """
        Remove log files older than 30 days.
        Called synchronously inside thread pool.
        """
        try:
            cutoff = datetime.utcnow().timestamp() - (30 * 24 * 3600)
            for log_file in self._log_dir.glob("transactions_*.log"):
                if log_file.stat().st_mtime < cutoff:
                    log_file.unlink()
        except OSError:
            pass  # Best-effort cleanup; do not crash on permission errors

    async def save(self, formatted_log: str) -> None:
        """
        Append a log entry to the current day's log file.

        Args:
            formatted_log: The formatted log string.
        """
        async with self._lock:
            log_file = self._get_log_file()
            # Run blocking file I/O in thread pool to keep event loop free
            await asyncio.to_thread(self._write_log, log_file, formatted_log)

    def _write_log(self, log_file: Path, formatted_log: str) -> None:
        """Synchronous file write helper."""
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(formatted_log + "\n")
            f.flush()
        self._cleanup_old_logs()

    async def close(self) -> None:
        """No-op for file repository; files are opened per-write."""
        pass
