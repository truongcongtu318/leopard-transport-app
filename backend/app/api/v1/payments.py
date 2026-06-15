"""
Payment routes — fare calculation, VietQR generation, payment status.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.payment import (
    FareCalcRequest,
    FareCalcResponse,
    VietQRRequest,
    VietQRResponse,
)
from app.services.payment_service import PaymentService
from app.services.pricing_service import PricingService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/fare/calculate",
    response_model=FareCalcResponse,
    summary="Calculate estimated fare",
)
async def calculate_fare(
    body: FareCalcRequest,
    db: AsyncSession = Depends(get_db),
) -> FareCalcResponse:
    """Calculate an estimated fare for a potential booking."""
    service = PricingService(db)
    fare = await service.calculate_fare(
        origin_lat=body.origin_lat,
        origin_lng=body.origin_lng,
        destination_lat=body.destination_lat,
        destination_lng=body.destination_lng,
        cargo_type=body.cargo_type,
        total_weight_kg=body.total_weight_kg,
        total_volume_cbm=body.total_volume_cbm,
        vehicle_type=body.vehicle_type,
        stops_count=body.stops_count,
    )
    return fare


@router.post(
    "/vietqr",
    response_model=VietQRResponse,
    summary="Generate VietQR code for payment",
)
async def generate_vietqr(
    body: VietQRRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> VietQRResponse:
    """Generate a VietQR payment code for an order."""
    service = PaymentService(db)
    qr_response = await service.generate_vietqr(
        order_id=body.order_id,
        amount=body.amount,
        payer_id=current_user.id,
        bank_code=body.bank_code,
        account_number=body.account_number,
        description=body.description,
    )
    return qr_response


@router.get(
    "/{payment_id}",
    summary="Get payment status",
)
async def get_payment_status(
    payment_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the status of a specific payment."""
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.payer_id != current_user.id and current_user.role not in ("admin", "fleet_owner"):
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "id": str(payment.id),
        "order_id": str(payment.order_id),
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


@router.get(
    "/orders/{order_id}",
    summary="List payments for an order",
)
async def list_order_payments(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all payments for a specific order."""
    service = PaymentService(db)
    payments = await service.list_order_payments(order_id)
    return [
        {
            "id": str(p.id),
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "payment_method": p.payment_method,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payments
    ]
