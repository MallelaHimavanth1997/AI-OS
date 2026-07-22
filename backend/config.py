"""Application settings for AI-OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import os
from typing import Final

from dotenv import load_dotenv


load_dotenv()

_TRUE_VALUES: Final[set[str]] = {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AppSettings:
    """Centralized configuration loaded from environment variables."""

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "AI-OS"))
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    app_host: str = field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    app_port: int = field(default_factory=lambda: int(os.getenv("APP_PORT", "8000")))
    debug: bool = field(default_factory=lambda: os.getenv("APP_DEBUG", "false").lower() in _TRUE_VALUES)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_dir: Path = field(default_factory=lambda: Path(os.getenv("LOG_DIR", "logs")).expanduser())
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql+asyncpg://ai_os:change-me@localhost:5432/ai_os"))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me"))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_access_token_expire_minutes: int = field(default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
    workday_start: str = field(default_factory=lambda: os.getenv("WORKDAY_START", "07:00"))
    workday_end: str = field(default_factory=lambda: os.getenv("WORKDAY_END", "21:00"))

    def ensure_runtime_directories(self) -> None:
        """Create required runtime directories when the app boots."""

        self.log_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return a cached settings instance for dependency injection."""

    settings = AppSettings()
    settings.ensure_runtime_directories()
    return settings
