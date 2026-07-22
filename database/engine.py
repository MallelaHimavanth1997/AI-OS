"""Async SQLAlchemy engine and session management for AI-OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine as sa_create_async_engine

from .config import DatabaseSettings, get_database_settings


def create_async_engine(settings: DatabaseSettings | None = None) -> AsyncEngine:
    """Create a configured SQLAlchemy async engine."""

    db_settings = settings or get_database_settings()
    return sa_create_async_engine(
        db_settings.database_url,
        echo=db_settings.database_echo,
        pool_size=db_settings.pool_size,
        max_overflow=db_settings.max_overflow,
        pool_timeout=db_settings.pool_timeout,
        pool_recycle=db_settings.pool_recycle,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine | None = None, settings: DatabaseSettings | None = None) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the database engine."""

    db_settings = settings or get_database_settings()
    bound_engine = engine or create_async_engine(db_settings)
    return async_sessionmaker(bound_engine, expire_on_commit=False)


@dataclass(slots=True)
class DatabaseManager:
    """Small helper that owns the engine and session factory."""

    settings: DatabaseSettings

    def __post_init__(self) -> None:
        self.engine = create_async_engine(self.settings)
        self.session_factory = create_session_factory(self.engine, self.settings)

    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield an async session and manage its lifecycle."""

        async with self.session_factory() as session:
            yield session