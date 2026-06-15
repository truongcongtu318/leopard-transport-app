"""
Vehicle schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


VehicleTypeEnum = Literal[
    "three_wheeler",
    "truck_under_2t",
    "truck_2t_5t",
    "truck_5t_10t",
    "truck_over_10t",
    "container",
]


class VehicleCreate(BaseModel):
    """Create a new vehicle."""

    license_plate: str = Field(..., max_length=15)
    vehicle_type: VehicleTypeEnum
    brand: str | None = None
    model: str | None = None
    year_of_manufacture: int | None = None
    max_payload_kg: float = Field(..., gt=0)
    max_volume_cbm: float | None = None
    length_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None
    features: list[str] | None = None


class VehicleRead(BaseModel):
    """Vehicle record returned to clients."""

    id: uuid.UUID
    owner_id: uuid.UUID
    license_plate: str
    vehicle_type: str
    brand: str | None = None
    model: str | None = None
    year_of_manufacture: int | None = None
    max_payload_kg: float
    max_volume_cbm: float | None = None
    length_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None
    status: str
    images: list | None = None
    features: list | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VehicleUpdate(BaseModel):
    """Updateable vehicle fields."""

    brand: str | None = None
    model: str | None = None
    max_payload_kg: float | None = None
    max_volume_cbm: float | None = None
    length_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None
    status: str | None = None
    features: list[str] | None = None
