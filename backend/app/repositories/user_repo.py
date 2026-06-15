"""
User repository — specialised queries for the User model.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model with custom queries."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_phone(self, db: AsyncSession, phone_number: str) -> User | None:
        """Find a user by phone number."""
        result = await db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Find a user by email."""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_firebase_uid(
        self, db: AsyncSession, firebase_uid: str
    ) -> User | None:
        """Find a user by Firebase UID."""
        result = await db.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        return result.scalar_one_or_none()

    async def list_by_role(
        self,
        db: AsyncSession,
        role: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """List all users with a specific role."""
        result = await db.execute(
            select(User)
            .where(User.role == role, User.is_active == True)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 20,
    ) -> list[User]:
        """Search users by name, email, or phone number."""
        like_pattern = f"%{query}%"
        result = await db.execute(
            select(User)
            .where(
                (User.full_name.ilike(like_pattern))
                | (User.email.ilike(like_pattern))
                | (User.phone_number.ilike(like_pattern))
            )
            .limit(limit)
        )
        return list(result.scalars().all())
