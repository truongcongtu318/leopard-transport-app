"""
ETA prediction schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ETAPredictRequest(BaseModel):
    """Request ETA prediction for a route segment."""

    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lng: float = Field(..., ge=-180, le=180)
    vehicle_type: str | None = None
    cargo_weight_kg: float | None = None
    departure_time: datetime | None = None
    order_id: uuid.UUID | None = None


class ETAPredictResponse(BaseModel):
    """ETA prediction result."""

    predicted_duration_min: int
    predicted_arrival: datetime
    distance_km: float
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    model_version: str = "xgboost-v1"
    weather_impact_pct: float = 0.0
    traffic_impact_pct: float = 0.0
    factors: dict = Field(
        default_factory=dict,
        description="Breakdown of contributing factors",
    )
