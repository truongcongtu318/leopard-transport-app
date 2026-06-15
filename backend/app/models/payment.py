"""
Payment model.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint(
            "payment_method IN ('vietqr', 'cash', 'bank_transfer', 'momo', 'zalopay')",
            name="CHK_payments_payment_method",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'refunded')",
            name="CHK_payments_status",
        ),
        Index("IX_payments_order_id", "order_id"),
        Index("IX_payments_payer_id", "payer_id"),
        Index("IX_payments_payee_id", "payee_id"),
        Index("IX_payments_status", "status"),
        Index("IX_payments_transaction_id", "transaction_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", name="FK_payments_order_id"),
        nullable=False,
    )
    payer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_payments_payer_id"),
        nullable=False,
    )
    payee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_payments_payee_id"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="VND"
    )
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    transaction_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    vietqr_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_metadata: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="payments")
    payer = relationship("User", foreign_keys=[payer_id], lazy="noload")
    payee = relationship("User", foreign_keys=[payee_id], lazy="noload")

    def __repr__(self) -> str:
        return f"<Payment {self.amount} {self.currency} ({self.status})>"
