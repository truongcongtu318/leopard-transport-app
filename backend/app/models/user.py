"""
User model — covers shippers, drivers, fleet owners, and admins.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('shipper', 'driver', 'fleet_owner', 'admin')",
            name="CHK_users_role",
        ),
        CheckConstraint(
            "auth_provider IN ('phone', 'google', 'email')",
            name="CHK_users_auth_provider",
        ),
        Index("IX_users_phone", "phone_number"),
        Index("IX_users_email", "email"),
        Index("IX_users_firebase_uid", "firebase_uid"),
        Index("IX_users_role", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    firebase_uid: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(15), unique=True, nullable=True
    )
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="shipper"
    )
    auth_provider: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="phone"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    driver = relationship("Driver", back_populates="user", uselist=False, lazy="selectin")
    orders = relationship("Order", back_populates="shipper", lazy="noload", foreign_keys="Order.shipper_id")
    notifications = relationship("Notification", back_populates="user", lazy="noload")

    def __repr__(self) -> str:
        return f"<User {self.full_name} ({self.role})>"
