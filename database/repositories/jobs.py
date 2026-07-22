"""Job repository built on the shared async repository base."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from ..models import Job
from .base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Persistence operations for jobs and associated search data."""

    async def get_by_external_key(self, source_name: str, external_job_id: str) -> Job | None:
        statement = select(Job).where(Job.source_name == source_name, Job.external_job_id == external_job_id)
        return await self.first(statement)

    async def get_by_id(self, job_id: UUID) -> Job | None:
        return await self.first(select(Job).where(Job.id == job_id))