"""
Payment repository — specialised queries for payments.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.base_repo import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment model with custom queries."""

    def __init__(self) -> None:
        super().__init__(Payment)

    async def get_by_transaction_id(
        self, db: AsyncSession, transaction_id: str
    ) -> Payment | None:
        """Find a payment by its transaction ID."""
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def list_by_order(
        self,
        db: AsyncSession,
        order_id: uuid.UUID,
    ) -> list[Payment]:
        """List all payments for a specific order."""
        result = await db.execute(
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_payer(
        self,
        db: AsyncSession,
        payer_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        """List all payments made by a specific user."""
        result = await db.execute(
            select(Payment)
            .where(Payment.payer_id == payer_id)
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def sum_revenue(
        self,
        db: AsyncSession,
        since: datetime | None = None,
    ) -> float:
        """Sum total revenue from completed payments."""
        stmt = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.status == "completed"
        )
        if since:
            stmt = stmt.where(Payment.paid_at >= since)
        result = await db.scalar(stmt)
        return float(result or 0.0)

    async def count_pending(self, db: AsyncSession) -> int:
        """Count payments in pending status."""
        result = await db.scalar(
            select(func.count(Payment.id)).where(Payment.status == "pending")
        )
        return result or 0
