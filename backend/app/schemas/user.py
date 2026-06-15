"""
User schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    """Public user profile."""

    id: uuid.UUID
    phone_number: str | None = None
    email: str | None = None
    full_name: str
    avatar_url: str | None = None
    role: str
    auth_provider: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Fields that a user may update on their own profile."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    avatar_url: str | None = None
