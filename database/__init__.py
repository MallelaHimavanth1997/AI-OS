"""PostgreSQL database foundation for AI-OS."""

from .config import DatabaseSettings, get_database_settings
from .engine import DatabaseManager, create_async_engine, create_session_factory
from .models import (
    Application,
    Base,
    Company,
    CoverLetter,
    DashboardMetric,
    Email,
    HistoryEntry,
    Job,
    Notification,
    Recruiter,
    Resume,
    User,
)

__all__ = [
    "Application",
    "Base",
    "Company",
    "CoverLetter",
    "DashboardMetric",
    "DatabaseManager",
    "DatabaseSettings",
    "Email",
    "HistoryEntry",
    "Job",
    "Notification",
    "Recruiter",
    "Resume",
    "User",
    "create_async_engine",
    "create_session_factory",
    "get_database_settings",
]