"""Centralized logging configuration."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    *,
    log_dir: Path | None = None,
    app_name: str = "election_platform",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    log_to_file: bool = True,
) -> None:
    """Configure console (and optional rotating file) log handlers.

    On platforms like Render, prefer stdout-only logging (`log_to_file=False`).
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Quiet noisy third-party loggers in production-friendly defaults.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if not log_to_file or log_dir is None:
        return

    log_dir.mkdir(parents=True, exist_ok=True)
    categories = ("application", "authentication", "database", "synchronization", "errors")
    for category in categories:
        file_handler = RotatingFileHandler(
            log_dir / f"{app_name}_{category}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        category_logger = logging.getLogger(f"{app_name}.{category}")
        category_logger.addHandler(file_handler)
        category_logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
