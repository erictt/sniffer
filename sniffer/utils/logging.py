"""
Modern logging configuration for Sniffer application using Loguru.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger
from ..config.constants import (
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE,
    LOG_ROTATION,
    LOG_RETENTION,
    LOG_COLORIZE,
)


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    colorize: Optional[bool] = None,
    rotation: Optional[str] = None,
    retention: Optional[str] = None,
    format_str: Optional[str] = None,
) -> None:
    """
    Configure logging for the application using Loguru.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        colorize: Whether to colorize console output
        rotation: Log rotation setting (e.g., "10 MB", "1 day")
        retention: Log retention setting (e.g., "10 days", "1 week")
        format_str: Custom log format string
    """
    # Use config defaults if not provided
    level = level or LOG_LEVEL
    log_file = log_file or LOG_FILE
    colorize = colorize if colorize is not None else LOG_COLORIZE
    rotation = rotation or LOG_ROTATION
    retention = retention or LOG_RETENTION
    format_str = format_str or LOG_FORMAT

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(sys.stderr, level=level, format=format_str, colorize=colorize)

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_path),
            level=level,
            format=format_str,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )


def get_logger(name: str = "sniffer"):
    """
    Get a logger instance.

    Args:
        name: Logger name (for context, Loguru uses single global logger)

    Returns:
        Loguru logger with context
    """
    return logger.bind(name=name)


# Progress logger for CLI operations
class ProgressLogger:
    """Logger specifically for progress tracking using Loguru."""

    def __init__(self, name: str = "sniffer.progress"):
        self.logger = logger.bind(name=name)

    def start_operation(
        self, operation: str, total_items: Optional[int] = None
    ) -> None:
        """Log the start of an operation."""
        if total_items:
            self.logger.info(f"Starting {operation} - {total_items} items to process")
        else:
            self.logger.info(f"Starting {operation}")

    def progress_update(
        self,
        operation: str,
        current: int,
        total: Optional[int] = None,
        message: str = "",
    ) -> None:
        """Log progress update."""
        if total:
            percentage = (current / total) * 100
            self.logger.info(
                f"{operation}: {current}/{total} ({percentage:.1f}%) {message}"
            )
        else:
            self.logger.info(f"{operation}: {current} processed {message}")

    def complete_operation(
        self, operation: str, total_processed: int, duration: Optional[float] = None
    ) -> None:
        """Log operation completion."""
        if duration:
            self.logger.success(
                f"Completed {operation} - {total_processed} items processed in {duration:.2f}s"
            )
        else:
            self.logger.success(
                f"Completed {operation} - {total_processed} items processed"
            )

    def operation_error(
        self, operation: str, error: str, item: Optional[str] = None
    ) -> None:
        """Log operation error."""
        if item:
            self.logger.error(f"{operation} failed for {item}: {error}")
        else:
            self.logger.error(f"{operation} failed: {error}")


# Convenience function for quick setup
def setup_default_logging() -> None:
    """Setup default logging configuration from environment variables."""
    setup_logging()


# Global logger instance
log = get_logger()
