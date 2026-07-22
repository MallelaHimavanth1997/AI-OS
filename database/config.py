"""Database configuration for the PostgreSQL persistence layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class DatabaseSettings:
    """Configuration values for the PostgreSQL database stack."""

    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://ai_os:change-me@localhost:5432/ai_os",
        )
    )
    database_echo: bool = field(default_factory=lambda: os.getenv("DATABASE_ECHO", "false").lower() in {"1", "true", "yes", "on"})
    pool_size: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "10")))
    max_overflow: int = field(default_factory=lambda: int(os.getenv("DATABASE_MAX_OVERFLOW", "20")))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_TIMEOUT", "30")))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_RECYCLE", "1800")))
    statement_timeout_ms: int = field(default_factory=lambda: int(os.getenv("DATABASE_STATEMENT_TIMEOUT_MS", "30000")))
    schema_name: str = field(default_factory=lambda: os.getenv("DATABASE_SCHEMA", "public"))


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """Return cached database settings for dependency injection."""

    return DatabaseSettings()