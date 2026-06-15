"""
Tracking schemas — GPS location updates and tracking events.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LocationUpdate(BaseModel):
    """GPS location tick sent from driver app."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed_kmh: float | None = Field(default=None, ge=0)
    heading: float | None = Field(default=None, ge=0, le=360)
    accuracy_m: float | None = Field(default=None, ge=0)
    altitude_m: float | None = None
    battery_pct: int | None = Field(default=None, ge=0, le=100)
    timestamp: datetime | None = None
    order_id: uuid.UUID | None = None


class TrackingEvent(BaseModel):
    """Tracking event broadcast to subscribers."""

    driver_id: uuid.UUID
    order_id: uuid.UUID | None = None
    latitude: float
    longitude: float
    speed_kmh: float | None = None
    heading: float | None = None
    timestamp: datetime
    event_type: str = "location_update"

    model_config = {"from_attributes": True}
