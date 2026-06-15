"""
Notification and OrderStatusLog models.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('push', 'in_app', 'sms', 'email')",
            name="CHK_notifications_type",
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'critical')",
            name="CHK_notifications_priority",
        ),
        Index("IX_notifications_user_id", "user_id"),
        Index("IX_notifications_is_read", "is_read"),
        Index("IX_notifications_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_notifications_user_id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="in_app"
    )
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="normal"
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    action_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_payload: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fcm_message_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification '{self.title}' -> {self.user_id}>"


class OrderStatusLog(TimestampMixin, Base):
    __tablename__ = "order_status_logs"

    __table_args__ = (
        Index("IX_order_status_logs_order_id", "order_id"),
        Index("IX_order_status_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", name="FK_order_status_logs_order_id"),
        nullable=False,
    )
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_order_status_logs_changed_by"),
        nullable=True,
    )
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    # Relationships
    order = relationship("Order", back_populates="status_logs")
    user = relationship("User", foreign_keys=[changed_by], lazy="noload")

    def __repr__(self) -> str:
        return f"<OrderStatusLog {self.old_status} -> {self.new_status}>"
