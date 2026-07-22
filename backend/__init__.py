"""Backend foundation for AI-OS."""

from .app import create_app
from .config import AppSettings, get_settings

__all__ = ["AppSettings", "create_app", "get_settings"]
