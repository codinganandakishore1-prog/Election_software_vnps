"""Centralized logging configuration."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    *,
    log_dir: Path,
    app_name: str = "election_platform",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configure rotating file and console log handlers."""
    log_dir.mkdir(parents=True, exist_ok=True)

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

    categories = ("application", "authentication", "database", "synchronization", "errors")
    for category in categories:
        file_handler = RotatingFileHandler(
            log_dir / f"{app_name}_{category}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        logging.getLogger(f"{app_name}.{category}").addHandler(file_handler)
        logging.getLogger(f"{app_name}.{category}").propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
