"""
Base repository — generic async CRUD with SQLAlchemy 2.0 AsyncSession.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic CRUD repository for SQLAlchemy models.

    Usage::

        repo = BaseRepository(User)
        user = await repo.get(db, some_uuid)
        users = await repo.list_all(db, limit=20, offset=0)
    """

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, record_id: uuid.UUID) -> ModelT | None:
        """Get a single record by primary key."""
        result = await db.execute(
            select(self.model).where(self.model.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by(
        self, db: AsyncSession, filters: dict[str, Any]
    ) -> ModelT | None:
        """Get a single record matching all provided filter kwargs."""
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelT]:
        """List all records with pagination."""
        stmt = select(self.model).offset(offset).limit(limit)
        if hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_by(
        self,
        db: AsyncSession,
        filters: dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelT]:
        """List records matching provided filter kwargs."""
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        if hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, instance: ModelT) -> ModelT:
        """Insert a new record."""
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update(
        self,
        db: AsyncSession,
        instance: ModelT,
        update_data: dict[str, Any],
    ) -> ModelT:
        """Update an existing record with the provided key-value pairs."""
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def delete(self, db: AsyncSession, instance: ModelT) -> None:
        """Delete a record."""
        await db.delete(instance)
        await db.flush()

    async def count(
        self,
        db: AsyncSession,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Count records, optionally filtered."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        if filters:
            for key, value in filters.items():
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await db.scalar(stmt)
        return result or 0

    async def exists(
        self,
        db: AsyncSession,
        filters: dict[str, Any],
    ) -> bool:
        """Check whether at least one record matches the filters."""
        return (await self.count(db, filters)) > 0
