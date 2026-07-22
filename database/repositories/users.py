"""User repository built on the shared async repository base."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Persistence operations for users."""

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return await self.first(statement)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.first(select(User).where(User.id == user_id))