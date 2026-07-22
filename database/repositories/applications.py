"""Application repository built on the shared async repository base."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from ..models import Application
from .base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    """Persistence operations for application records."""

    async def get_by_id(self, application_id: UUID) -> Application | None:
        return await self.first(select(Application).where(Application.id == application_id))

    async def list_for_user(self, user_id: UUID, *, limit: int = 50) -> list[Application]:
        result = await self.session.execute(
            select(Application).where(Application.user_id == user_id).order_by(Application.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())