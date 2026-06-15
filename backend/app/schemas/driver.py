"""
Driver schemas.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class DriverRead(BaseModel):
    """Driver profile returned to clients."""

    id: uuid.UUID
    user_id: uuid.UUID
    license_number: str
    license_class: str
    license_expiry: date
    id_card_number: str
    status: str
    is_online: bool
    is_busy: bool
    rating: float
    total_trips: int
    vehicle_id: uuid.UUID | None = None
    business_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DriverUpdate(BaseModel):
    """Fields that a driver may update."""

    license_number: str | None = Field(default=None, max_length=20)
    license_class: str | None = Field(
        default=None,
        pattern=r"^(B2|C|D|E|FC)$",
    )
    license_expiry: date | None = None
    id_card_number: str | None = Field(default=None, max_length=20)
    is_online: bool | None = None


class DriverDocumentRead(BaseModel):
    """Driver document record."""

    id: uuid.UUID
    driver_id: uuid.UUID
    document_type: str
    file_url: str
    status: str
    review_note: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
