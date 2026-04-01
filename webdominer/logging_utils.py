from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from .settings import Settings


def configure_logging(settings: Settings) -> None:
    """
    Configure root logging for both console and file output.

    Safe to call multiple times; existing handlers will be replaced.
    """
    settings.ensure_directories()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicate logs.
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    file_handler = logging.FileHandler(settings.log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> Logger:
    """Return a logger with the provided module name."""
    return logging.getLogger(name)