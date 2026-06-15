"""
Order schemas — create, read, stop, item.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CargoTypeEnum = Literal[
    "general", "fragile", "perishable", "dangerous", "oversized"
]

OrderStatusEnum = Literal[
    "draft",
    "pending",
    "bidding",
    "accepted",
    "pickup_in_progress",
    "in_transit",
    "delivered",
    "completed",
    "cancelled",
    "disputed",
]


class OrderStopCreate(BaseModel):
    """A stop (pickup / dropoff / waypoint) within an order."""

    stop_type: Literal["pickup", "dropoff", "waypoint"]
    sequence: int = Field(..., ge=0)
    address: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    planned_arrival: datetime | None = None


class OrderItemCreate(BaseModel):
    """An item in the cargo manifest."""

    item_name: str = Field(..., max_length=255)
    quantity: int = Field(default=1, ge=1)
    weight_kg: float | None = None
    volume_cbm: float | None = None
    unit_value: float | None = None
    package_type: str | None = None
    is_fragile: bool = False


class OrderCreate(BaseModel):
    """Create a new order (booking)."""

    cargo_type: CargoTypeEnum = "general"
    total_weight_kg: float = Field(..., gt=0)
    total_volume_cbm: float | None = None
    cargo_value: float | None = None
    cargo_description: str | None = None
    special_instructions: str | None = None
    pickup_deadline: datetime | None = None
    delivery_deadline: datetime | None = None
    stops: list[OrderStopCreate] = Field(..., min_length=2)
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderStopRead(BaseModel):
    """Stop as returned from the API."""

    id: uuid.UUID
    stop_type: str
    sequence: int
    address: str
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    status: str
    planned_arrival: datetime | None = None
    actual_arrival: datetime | None = None
    actual_departure: datetime | None = None

    model_config = {"from_attributes": True}


class OrderItemRead(BaseModel):
    """Order item as returned from the API."""

    id: uuid.UUID
    item_name: str
    quantity: int
    weight_kg: float | None = None
    volume_cbm: float | None = None
    unit_value: float | None = None
    package_type: str | None = None
    is_fragile: bool

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    """Full order as returned from the API."""

    id: uuid.UUID
    shipper_id: uuid.UUID
    driver_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    tracking_code: str
    status: str
    cargo_type: str
    total_weight_kg: float
    total_volume_cbm: float | None = None
    cargo_value: float | None = None
    cargo_description: str | None = None
    estimated_distance_km: float | None = None
    estimated_duration_min: int | None = None
    base_fare: float | None = None
    final_fare: float | None = None
    currency: str
    pickup_deadline: datetime | None = None
    delivery_deadline: datetime | None = None
    actual_pickup_at: datetime | None = None
    actual_delivery_at: datetime | None = None
    stops: list[OrderStopRead] = []
    items: list[OrderItemRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    """Update an order's status (admin / driver action)."""

    status: OrderStatusEnum
    reason: str | None = None
