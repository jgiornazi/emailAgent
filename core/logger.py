"""
Logging and audit trail for EmailAgent.

Provides structured logging with:
- Rotating file handlers
- Console output with colors
- Separate audit logs for deletions
- Extraction and classification logs
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


# Global logger instance
_logger: Optional[logging.Logger] = None
_deletion_logger: Optional[logging.Logger] = None
_console = Console()


def setup_logger(
    name: str = "emailagent",
    level: str = "INFO",
    log_directory: Optional[Path] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    use_colors: bool = True,
    max_size_mb: int = 10,
) -> logging.Logger:
    """
    Set up the main application logger.

    Args:
        name: Logger name.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_directory: Directory for log files.
        log_to_file: Whether to log to file.
        log_to_console: Whether to log to console.
        use_colors: Whether to use colored console output.
        max_size_mb: Maximum log file size in MB before rotation.

    Returns:
        Configured logger instance.
    """
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    # File handler
    if log_to_file and log_directory:
        log_directory = Path(log_directory)
        log_directory.mkdir(parents=True, exist_ok=True)

        log_file = log_directory / f"emailagent_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Console handler
    if log_to_console:
        if use_colors:
            console_handler = RichHandler(
                console=_console,
                show_time=True,
                show_level=True,
                show_path=False,
                rich_tracebacks=True,
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%H:%M:%S",
            )
            console_handler.setFormatter(console_formatter)

        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the application logger.

    Args:
        name: Optional child logger name.

    Returns:
        Logger instance.
    """
    global _logger

    if _logger is None:
        _logger = setup_logger()

    if name:
        return _logger.getChild(name)
    return _logger


def setup_deletion_logger(
    log_directory: Path,
    max_size_mb: int = 10,
) -> logging.Logger:
    """
    Set up a separate logger for deletion audit trail.

    Args:
        log_directory: Directory for deletion log files.
        max_size_mb: Maximum log file size in MB.

    Returns:
        Configured deletion logger.
    """
    global _deletion_logger

    if _deletion_logger is not None:
        return _deletion_logger

    logger = logging.getLogger("emailagent.deletions")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    log_directory = Path(log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)

    log_file = log_directory / f"deletions_{datetime.now().strftime('%Y%m%d')}.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    _deletion_logger = logger
    return logger


def get_deletion_logger() -> logging.Logger:
    """Get the deletion audit logger."""
    global _deletion_logger
    if _deletion_logger is None:
        from .config import get_default_config_dir
        log_dir = get_default_config_dir() / "logs"
        _deletion_logger = setup_deletion_logger(log_dir)
    return _deletion_logger


def log_deletion(
    email_id: str,
    company: str,
    status: str,
    subject: str,
    timestamp: Optional[datetime] = None,
) -> None:
    """
    Log a single email deletion to the audit trail.

    Args:
        email_id: Gmail message ID.
        company: Company name.
        status: Email status (Applied, Rejected, etc.).
        subject: Email subject (truncated).
        timestamp: Deletion timestamp.
    """
    logger = get_deletion_logger()
    ts = timestamp or datetime.now()

    # Truncate subject for readability
    subject_short = subject[:50] + "..." if len(subject) > 50 else subject

    logger.info(
        f"DELETED | {email_id} | {company} | {status} | {subject_short}"
    )


def log_deletion_batch_start(total_count: int) -> None:
    """Log the start of a deletion batch."""
    logger = get_deletion_logger()
    logger.info(f"BATCH_START | Count: {total_count} | Time: {datetime.now().isoformat()}")


def log_deletion_batch_complete(deleted_count: int, failed_count: int = 0) -> None:
    """Log the completion of a deletion batch."""
    logger = get_deletion_logger()
    logger.info(
        f"BATCH_COMPLETE | Deleted: {deleted_count} | Failed: {failed_count} | "
        f"Time: {datetime.now().isoformat()}"
    )


def log_conflict(
    company: str,
    current_status: str,
    new_status: str,
    email_id: str,
) -> None:
    """
    Log a status conflict.

    Args:
        company: Company name.
        current_status: Current status in Excel.
        new_status: New status from email.
        email_id: Gmail message ID.
    """
    logger = get_logger("conflict")
    logger.warning(
        f"CONFLICT | Company: {company} | Current: {current_status} | "
        f"New: {new_status} | Email: {email_id}"
    )


def log_extraction(
    email_id: str,
    company: str,
    position: str,
    status: str,
    confidence: str,
    method: str,
) -> None:
    """
    Log extraction result.

    Args:
        email_id: Gmail message ID.
        company: Extracted company name.
        position: Extracted position.
        status: Classified status.
        confidence: Confidence level.
        method: Extraction method (pattern or ai).
    """
    logger = get_logger("extraction")
    logger.debug(
        f"EXTRACTED | {email_id} | Company: {company} | Position: {position} | "
        f"Status: {status} | Confidence: {confidence} | Method: {method}"
    )


def log_api_call(
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log a Gmail API call.

    Args:
        endpoint: API endpoint called.
        method: HTTP method.
        status_code: Response status code.
        error: Error message if failed.
    """
    logger = get_logger("api")
    if error:
        logger.error(f"API_CALL | {method} {endpoint} | Error: {error}")
    else:
        logger.debug(f"API_CALL | {method} {endpoint} | Status: {status_code}")


def cleanup_old_logs(log_directory: Path, retention_days: int = 30) -> int:
    """
    Clean up log files older than retention period.

    Args:
        log_directory: Directory containing log files.
        retention_days: Number of days to keep logs.

    Returns:
        Number of files deleted.
    """
    from datetime import timedelta

    log_directory = Path(log_directory)
    if not log_directory.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = 0

    for log_file in log_directory.glob("*.log*"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                log_file.unlink()
                deleted += 1
        except (OSError, PermissionError):
            continue

    if deleted > 0:
        get_logger().info(f"Cleaned up {deleted} old log files")

    return deleted
