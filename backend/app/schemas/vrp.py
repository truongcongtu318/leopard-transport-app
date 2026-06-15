"""
VRP optimisation schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VehicleDef(BaseModel):
    """Definition of a vehicle for the VRP solver."""

    vehicle_id: uuid.UUID | None = None
    start_lat: float = Field(..., ge=-90, le=90)
    start_lng: float = Field(..., ge=-180, le=180)
    max_payload_kg: float = Field(..., gt=0)
    max_volume_cbm: float | None = None
    fixed_cost: float = 0.0
    cost_per_km: float = 1.0


class StopDef(BaseModel):
    """A stop in the VRP problem."""

    stop_id: uuid.UUID | None = None
    name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    weight_kg: float = 0.0
    volume_cbm: float = 0.0
    service_duration_min: int = 15
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None


class VRPOptimizeRequest(BaseModel):
    """Request to solve a Vehicle Routing Problem."""

    vehicles: list[VehicleDef] = Field(..., min_length=1)
    stops: list[StopDef] = Field(..., min_length=2)
    depot_lat: float = Field(..., ge=-90, le=90)
    depot_lng: float = Field(..., ge=-180, le=180)
    solver_time_limit_s: int = Field(default=30, ge=1, le=300)
    priority: str = Field(default="distance", pattern="^(distance|time|cost)$")


class VehicleRoute(BaseModel):
    """A single vehicle's optimized route."""

    vehicle_id: uuid.UUID | None = None
    stop_order: list[int] = Field(..., description="Sequence of stop indices")
    distance_km: float
    duration_min: int
    load_kg: float


class VRPOptimizeResponse(BaseModel):
    """VRP optimisation result."""

    solver_status: str
    total_distance_km: float
    total_duration_min: float
    num_vehicles_used: int
    num_stops_optimized: int
    solver_time_ms: int
    routes: list[VehicleRoute] = []
    unassigned_stops: list[int] = []
    metadata: dict[str, Any] = {}
