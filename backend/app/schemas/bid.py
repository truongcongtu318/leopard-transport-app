"""
Bid schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BidCreate(BaseModel):
    """Driver submits a bid on an order."""

    bid_amount: float = Field(..., gt=0, description="Bid amount in VND")
    estimated_duration_min: int = Field(..., gt=0)
    bid_message: str | None = None


class BidRead(BaseModel):
    """Bid record returned to clients."""

    id: uuid.UUID
    order_id: uuid.UUID
    driver_id: uuid.UUID
    bid_amount: float
    estimated_duration_min: int
    bid_message: str | None = None
    status: str
    accepted_at: datetime | None = None
    rejected_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BidAccept(BaseModel):
    """Shipper accepts a bid."""

    bid_id: uuid.UUID
