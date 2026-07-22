"""Repository base classes for async PostgreSQL access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


ModelT = TypeVar("ModelT")


class RepositoryError(RuntimeError):
    """Raised when repository operations fail."""


@dataclass(slots=True)
class BaseRepository(Generic[ModelT]):
    """Reusable async repository helper built around an AsyncSession."""

    session: AsyncSession

    async def add(self, instance: ModelT) -> ModelT:
        try:
            self.session.add(instance)
            await self.session.flush()
            return instance
        except SQLAlchemyError as exc:  # pragma: no cover - translated error surface
            raise RepositoryError("Failed to add entity.") from exc

    async def delete(self, instance: ModelT) -> None:
        try:
            await self.session.delete(instance)
            await self.session.flush()
        except SQLAlchemyError as exc:  # pragma: no cover - translated error surface
            raise RepositoryError("Failed to delete entity.") from exc

    async def commit(self) -> None:
        try:
            await self.session.commit()
        except SQLAlchemyError as exc:  # pragma: no cover - translated error surface
            await self.session.rollback()
            raise RepositoryError("Failed to commit transaction.") from exc

    async def rollback(self) -> None:
        await self.session.rollback()

    async def scalar(self, statement: Select[tuple[ModelT]]):
        try:
            result = await self.session.scalar(statement)
            return result
        except SQLAlchemyError as exc:  # pragma: no cover - translated error surface
            raise RepositoryError("Failed to fetch scalar result.") from exc

    async def first(self, statement: Select[tuple[ModelT]]):
        try:
            result = await self.session.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as exc:  # pragma: no cover - translated error surface
            raise RepositoryError("Failed to fetch first result.") from exc

    def query_by_id(self, model: type[ModelT], entity_id) -> Select[tuple[ModelT]]:
        """Build a typed select statement for a model identifier."""

        return select(model).where(model.id == entity_id)