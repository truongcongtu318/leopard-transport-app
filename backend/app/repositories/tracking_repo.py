"""
Tracking repository — specialised queries for GPS tracking data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tracking import GPSTracking
from app.repositories.base_repo import BaseRepository


class TrackingRepository(BaseRepository[GPSTracking]):
    """Repository for GPSTracking model with time-series queries."""

    def __init__(self) -> None:
        super().__init__(GPSTracking)

    async def get_latest_for_driver(
        self,
        db: AsyncSession,
        driver_id: uuid.UUID,
    ) -> GPSTracking | None:
        """Get the most recent GPS tick for a driver."""
        result = await db.execute(
            select(GPSTracking)
            .where(GPSTracking.driver_id == driver_id)
            .order_by(GPSTracking.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_trail(
        self,
        db: AsyncSession,
        driver_id: uuid.UUID,
        since: datetime | None = None,
        limit: int = 200,
    ) -> list[GPSTracking]:
        """Get a GPS trail for a driver.

        If ``since`` is not provided, defaults to the last 2 hours.
        """
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=2)

        result = await db.execute(
            select(GPSTracking)
            .where(
                GPSTracking.driver_id == driver_id,
                GPSTracking.timestamp >= since,
            )
            .order_by(GPSTracking.timestamp.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_trail_for_order(
        self,
        db: AsyncSession,
        order_id: uuid.UUID,
        limit: int = 500,
    ) -> list[GPSTracking]:
        """Get the full GPS trail for an order."""
        result = await db.execute(
            select(GPSTracking)
            .where(GPSTracking.order_id == order_id)
            .order_by(GPSTracking.timestamp.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_insert(
        self,
        db: AsyncSession,
        records: list[dict],
    ) -> int:
        """Bulk insert GPS records using raw SQL (faster for high volume)."""
        if not records:
            return 0

        values_list: list[str] = []
        for r in records:
            values_list.append(
                f"('{r['driver_id']}', '{r.get('order_id', 'NULL')}', "
                f"ST_SetSRID(ST_MakePoint({r['longitude']}, {r['latitude']}), 4326), "
                f"{r['latitude']}, {r['longitude']}, "
                f"{r.get('speed_kmh', 'NULL')}, {r.get('heading', 'NULL')}, "
                f"{r.get('accuracy_m', 'NULL')}, {r.get('altitude_m', 'NULL')}, "
                f"{r.get('battery_pct', 'NULL')}, "
                f"'{r.get('timestamp', datetime.now(timezone.utc).isoformat())}')"
            )

        query = text(
            """
            INSERT INTO gps_tracking
                (driver_id, order_id, location, latitude, longitude,
                 speed_kmh, heading, accuracy_m, altitude_m, battery_pct, timestamp)
            VALUES
            """
            + ",\n".join(values_list)
        )

        result = await db.execute(query)
        await db.flush()
        return result.rowcount
