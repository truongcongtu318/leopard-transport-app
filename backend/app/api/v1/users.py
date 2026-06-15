"""
User profile routes — read / update own profile.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserRead, summary="Get current user profile")
async def get_my_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserRead, summary="Update current user profile")
async def update_my_profile(
    body: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update the authenticated user's profile fields."""
    service = UserService(db)
    updated_user = await service.update_profile(current_user.id, body)
    return updated_user
