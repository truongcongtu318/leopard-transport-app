"""
User service — profile get/update, driver profile management.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.user import User
from app.schemas.driver import DriverUpdate
from app.schemas.user import UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """Business logic for user and driver profile operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_profile(self, user_id: uuid.UUID) -> User:
        """Get a user profile by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_profile(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        """Update a user's editable profile fields."""
        user = await self.get_profile(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_driver_profile(self, user: User) -> Driver:
        """Get the driver profile associated with a user."""
        if user.role != "driver":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a driver",
            )
        result = await self.db.execute(
            select(Driver).where(Driver.user_id == user.id)
        )
        driver = result.scalar_one_or_none()
        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Driver profile not found. Please complete registration.",
            )
        return driver

    async def update_driver_profile(
        self, user: User, data: DriverUpdate
    ) -> Driver:
        """Update a driver's profile fields."""
        driver = await self.get_driver_profile(user)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(driver, field, value)
        self.db.add(driver)
        await self.db.flush()
        await self.db.refresh(driver)
        return driver

    async def set_driver_online(self, user: User, is_online: bool) -> None:
        """Toggle a driver's online status."""
        driver = await self.get_driver_profile(user)
        driver.is_online = is_online
        if not is_online:
            driver.is_busy = False
        self.db.add(driver)
        await self.db.flush()
