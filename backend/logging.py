"""Loguru-based logging configuration for AI-OS."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

from loguru import logger

from .config import AppSettings


_LOGGER_READY = False


def configure_logging(settings: AppSettings) -> None:
    """Configure application-wide logging exactly once."""

    global _LOGGER_READY
    if _LOGGER_READY:
        return

    settings.ensure_runtime_directories()
    logger.remove()
    logger.add(sys.stdout, level=settings.log_level, enqueue=True, backtrace=False, diagnose=False)
    logger.add(
        Path(settings.log_dir) / "ai-os.log",
        level=settings.log_level,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
    _LOGGER_READY = True


def get_logger(*, bind: dict[str, Any] | None = None):
    """Return a logger instance optionally bound with contextual data."""

    contextual_logger = logger
    if bind:
        contextual_logger = contextual_logger.bind(**bind)
    return contextual_logger
