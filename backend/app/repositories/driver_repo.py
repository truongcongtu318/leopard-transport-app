"""
Driver repository — spatial queries for nearby drivers.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.repositories.base_repo import BaseRepository


class DriverRepository(BaseRepository[Driver]):
    """Repository for Driver model with spatial query support."""

    def __init__(self) -> None:
        super().__init__(Driver)

    async def find_nearby_drivers(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        vehicle_type: str | None = None,
        limit: int = 20,
    ) -> list[Driver]:
        """Find approved, online drivers within a given radius of a location.

        Uses PostGIS ``ST_DWithin`` for spatial indexing via GiST.
        """
        point_wkt = f"SRID=4326;POINT({longitude} {latitude})"

        stmt = select(Driver).where(
            Driver.status == "approved",
            Driver.is_online == True,
            Driver.is_busy == False,
            text(
                "ST_DWithin(current_location, "
                f"ST_GeomFromEWKT('{point_wkt}'), "
                f"{radius_km * 1000})"
            ),
        )

        if vehicle_type:
            # Filter drivers who have a vehicle of the requested type
            stmt = stmt.join(
                Driver.vehicle
            ).where(
                text(f"vehicles.vehicle_type = '{vehicle_type}'")
            )

        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def find_nearby_drivers_with_distance(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 20,
    ) -> list[dict]:
        """Find nearby drivers with computed distance.

        Returns list of dicts with driver info and distance_km field.
        """
        point_wkt = f"SRID=4326;POINT({longitude} {latitude})"

        query = text(
            """
            SELECT
                d.id,
                d.user_id,
                d.license_number,
                d.license_class,
                d.rating,
                d.total_trips,
                ST_X(d.current_location::geometry) AS lng,
                ST_Y(d.current_location::geometry) AS lat,
                ST_Distance(
                    d.current_location,
                    ST_GeomFromEWKT(:point_wkt)
                ) / 1000.0 AS distance_km
            FROM drivers d
            WHERE d.status = 'approved'
              AND d.is_online = true
              AND d.is_busy = false
              AND ST_DWithin(
                    d.current_location,
                    ST_GeomFromEWKT(:point_wkt),
                    :radius_m
              )
            ORDER BY distance_km ASC
            LIMIT :limit
        """
        )

        result = await db.execute(
            query,
            {
                "point_wkt": point_wkt,
                "radius_m": radius_km * 1000,
                "limit": limit,
            },
        )
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    async def update_location(
        self,
        db: AsyncSession,
        driver_id: uuid.UUID,
        latitude: float,
        longitude: float,
    ) -> None:
        """Update a driver's current location using PostGIS."""
        point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
        await db.execute(
            text(
                """
                UPDATE drivers
                SET current_location = ST_GeomFromEWKT(:point_wkt),
                    updated_at = NOW()
                WHERE id = :driver_id
            """
            ),
            {"point_wkt": point_wkt, "driver_id": driver_id},
        )
        await db.flush()

    async def get_online_drivers(
        self,
        db: AsyncSession,
        limit: int = 100,
    ) -> list[Driver]:
        """List all currently online approved drivers."""
        result = await db.execute(
            select(Driver)
            .where(Driver.status == "approved", Driver.is_online == True)
            .limit(limit)
        )
        return list(result.scalars().all())
