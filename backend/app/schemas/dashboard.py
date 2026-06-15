"""
Dashboard schemas — fleet statistics, active drivers, revenue breakdown.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ActiveDriverInfo(BaseModel):
    """Active driver summary for fleet dashboard."""

    driver_id: uuid.UUID
    full_name: str
    license_plate: str | None = None
    vehicle_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_busy: bool = False
    current_order_tracking_code: str | None = None
    last_update: datetime | None = None


class RevenueBreakdown(BaseModel):
    """Revenue breakdown for dashboard."""

    today_revenue: float = 0.0
    week_revenue: float = 0.0
    month_revenue: float = 0.0
    total_orders_today: int = 0
    total_orders_week: int = 0
    total_orders_month: int = 0
    currency: str = "VND"


class FleetStats(BaseModel):
    """Fleet-wide statistics for admin dashboard."""

    total_orders: int = 0
    active_orders: int = 0
    completed_orders_today: int = 0
    cancelled_orders_today: int = 0
    total_drivers: int = 0
    active_drivers: int = 0
    pending_documents: int = 0
    total_vehicles: int = 0
    active_vehicles: int = 0
    average_driver_rating: float = 0.0
    revenue: RevenueBreakdown = RevenueBreakdown()
    active_drivers_list: list[ActiveDriverInfo] = []
    order_status_distribution: dict[str, int] = {}
