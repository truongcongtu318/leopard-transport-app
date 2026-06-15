"""
Dashboard routes — fleet statistics for admins and fleet owners.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.models.driver import Driver, DriverDocument
from app.models.order import Order
from app.models.vehicle import Vehicle
from app.schemas.dashboard import (
    ActiveDriverInfo,
    FleetStats,
    RevenueBreakdown,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/fleet", response_model=FleetStats, summary="Get fleet-wide statistics")
async def get_fleet_stats(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> FleetStats:
    """Return fleet statistics for admins and fleet owners."""
    # Total orders
    total_orders = await db.scalar(
        select(func.count(Order.id))
    )
    active_orders = await db.scalar(
        select(func.count(Order.id)).where(
            Order.status.in_(["pending", "bidding", "accepted", "pickup_in_progress", "in_transit"])
        )
    )

    # Drivers
    total_drivers = await db.scalar(select(func.count(Driver.id)))
    active_drivers_count = await db.scalar(
        select(func.count(Driver.id)).where(Driver.is_online == True)
    )
    pending_documents = await db.scalar(
        select(func.count(DriverDocument.id)).where(DriverDocument.status == "pending")
    )
    avg_rating = await db.scalar(select(func.avg(Driver.rating))) or 0.0

    # Vehicles
    total_vehicles = await db.scalar(select(func.count(Vehicle.id)))
    active_vehicles = await db.scalar(
        select(func.count(Vehicle.id)).where(Vehicle.status == "active")
    )

    # Active drivers list
    active_drivers_result = await db.execute(
        select(Driver).where(Driver.is_online == True).limit(20)
    )
    active_drivers_list: list[ActiveDriverInfo] = []
    for d in active_drivers_result.scalars().all():
        lat, lng = None, None
        if d.current_location is not None:
            # WKB point extraction — simplified
            pass
        active_drivers_list.append(
            ActiveDriverInfo(
                driver_id=d.id,
                full_name=d.user.full_name if d.user else "N/A",
                license_plate=d.vehicle.license_plate if d.vehicle else None,
                vehicle_type=d.vehicle.vehicle_type if d.vehicle else None,
                latitude=lat,
                longitude=lng,
                is_busy=d.is_busy,
            )
        )

    # Order status distribution
    stmt = (
        select(Order.status, func.count(Order.id))
        .group_by(Order.status)
    )
    status_result = await db.execute(stmt)
    status_dist = {row[0]: row[1] for row in status_result.all()}

    # Revenue (simplified — sum of all payments)
    from app.models.payment import Payment
    today_start = func.date_trunc("day", func.now())
    today_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.status == "completed",
            Payment.paid_at >= today_start,
        )
    ) or 0.0

    month_start = func.date_trunc("month", func.now())
    month_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.status == "completed",
            Payment.paid_at >= month_start,
        )
    ) or 0.0

    return FleetStats(
        total_orders=total_orders or 0,
        active_orders=active_orders or 0,
        total_drivers=total_drivers or 0,
        active_drivers=active_drivers_count or 0,
        pending_documents=pending_documents or 0,
        total_vehicles=total_vehicles or 0,
        active_vehicles=active_vehicles or 0,
        average_driver_rating=round(float(avg_rating), 1),
        revenue=RevenueBreakdown(
            today_revenue=float(today_revenue),
            month_revenue=float(month_revenue),
        ),
        active_drivers_list=active_drivers_list,
        order_status_distribution=status_dist,
    )
