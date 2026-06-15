"""
Payment schemas — VietQR generation, fare calculation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FareCalcRequest(BaseModel):
    """Calculate fare for a potential booking."""

    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lng: float = Field(..., ge=-180, le=180)
    cargo_type: str = "general"
    total_weight_kg: float = Field(..., gt=0)
    total_volume_cbm: float | None = None
    vehicle_type: str | None = None
    stops_count: int = Field(default=2, ge=2)


class FareCalcResponse(BaseModel):
    """Fare estimation result."""

    distance_km: float
    duration_min: int
    base_rate: float
    weight_surcharge: float
    volume_surcharge: float = 0.0
    fuel_surcharge: float
    toll_fee_estimate: float = 0.0
    subtotal: float
    vat_pct: float = 8.0
    vat_amount: float
    total: float
    currency: str = "VND"
    breakdown: dict[str, Any] = {}


class VietQRRequest(BaseModel):
    """Request to generate a VietQR payment code."""

    order_id: uuid.UUID
    amount: float = Field(..., gt=0)
    bank_code: str | None = Field(
        default=None,
        description="Bank BIN code; defaults to configured bank",
    )
    account_number: str | None = Field(
        default=None,
        description="Recipient account number; defaults to platform account",
    )
    description: str | None = Field(
        default=None,
        max_length=25,
        description="Transfer description (max 25 chars per VietQR)",
    )


class VietQRResponse(BaseModel):
    """Generated VietQR payment information."""

    qr_code_base64: str
    transaction_id: str
    payment_url: str | None = None
    bank_code: str
    account_number: str
    account_name: str
    amount: float
    description: str
    expires_at: datetime
