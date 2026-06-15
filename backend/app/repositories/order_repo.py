"""
Order repository — specialised queries for orders.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderBid
from app.repositories.base_repo import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for Order model with custom queries."""

    def __init__(self) -> None:
        super().__init__(Order)

    async def get_by_tracking_code(
        self, db: AsyncSession, tracking_code: str
    ) -> Order | None:
        """Find an order by its tracking code."""
        result = await db.execute(
            select(Order).where(Order.tracking_code == tracking_code)
        )
        return result.scalar_one_or_none()

    async def list_by_shipper(
        self,
        db: AsyncSession,
        shipper_id: uuid.UUID,
        status_filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Order]:
        """List orders for a specific shipper."""
        stmt = select(Order).where(Order.shipper_id == shipper_id)
        if status_filter:
            stmt = stmt.where(Order.status == status_filter)
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_driver(
        self,
        db: AsyncSession,
        driver_id: uuid.UUID,
        status_filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Order]:
        """List orders assigned to a specific driver."""
        stmt = select(Order).where(Order.driver_id == driver_id)
        if status_filter:
            stmt = stmt.where(Order.status == status_filter)
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_available_for_bidding(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> list[Order]:
        """List orders available for driver bidding."""
        result = await db.execute(
            select(Order)
            .where(Order.status.in_(["pending", "bidding"]))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(
        self,
        db: AsyncSession,
    ) -> dict[str, int]:
        """Count orders grouped by status."""
        result = await db.execute(
            select(Order.status, func.count(Order.id)).group_by(Order.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def count_completed_today(self, db: AsyncSession) -> int:
        """Count orders completed today."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await db.scalar(
            select(func.count(Order.id)).where(
                Order.status == "completed",
                Order.updated_at >= today_start,
            )
        )
        return result or 0

    async def get_recent_orders(
        self,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 100,
    ) -> list[Order]:
        """Get orders created in the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await db.execute(
            select(Order)
            .where(Order.created_at >= cutoff)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
