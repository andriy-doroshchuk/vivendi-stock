"""Logging configuration module."""
import logging
import logging.handlers
from pathlib import Path

from .config import config


def setup_logger(
    name: str,
    log_level: str | None = None,
    log_dir: Path | None = None
) -> logging.Logger:
    """Configure and return a logger instance."""
    log_level = log_level or config.LOG_LEVEL
    log_dir = log_dir or config.LOG_DIR

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if logger.handlers:
        return logger

    log_file = log_dir / f'{name}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    formatter = logging.Formatter(config.LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


root_logger = setup_logger('vivendi-stock')
