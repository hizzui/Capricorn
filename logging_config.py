"""
Logging configuration for console output and rotating file logs.
"""

from __future__ import annotations

import logging
import logging.handlers

from config import Config


def setup_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return

    root_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(Config.LOG_FORMAT)

    console_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    try:
        Config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB per file
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError as exc:
        root_logger.warning("Could not attach file log handler (%s); continuing with stdout only.", exc)

    # Keep discord.py gateway/HTTP noise at WARNING level
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
