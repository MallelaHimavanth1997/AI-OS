"""Logger utility for AI-OS using loguru."""

import sys
from pathlib import Path
from loguru import logger

# Base directory and log file path
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "ai-os.log"

_is_configured = False


def _configure_logger() -> None:
    """Configure loguru sinks for console and file output."""
    global _is_configured
    if _is_configured:
        return

    # Remove default handler
    logger.remove()

    # Define log formats
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[name]}</cyan> - <level>{message}</level>"
    )

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[name]} - {message}"
    )

    # Console sink
    logger.add(
        sys.stdout,
        format=console_format,
        level="INFO",
        colorize=True,
    )

    # File sink
    logger.add(
        str(LOG_FILE),
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        enqueue=True,
    )

    _is_configured = True


def get_logger(name: str = "AI-OS"):
    """Get a configured loguru logger bound to the specified module/component name.

    Args:
        name (str): Name of the component or module requesting the logger.

    Returns:
        loguru.Logger: Logger instance bound with extra context.
    """
    _configure_logger()
    return logger.bind(name=name)
