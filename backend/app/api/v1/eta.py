"""
ETA prediction endpoint.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.eta import ETAPredictRequest, ETAPredictResponse
from app.services.eta_service import ETAService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/predict",
    response_model=ETAPredictResponse,
    summary="Predict ETA for a delivery route",
)
async def predict_eta(
    body: ETAPredictRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ETAPredictResponse:
    """Predict the estimated time of arrival for a delivery route.

    Uses an XGBoost model with fallback to haversine-based estimation.
    """
    service = ETAService(db)
    result = await service.predict(
        origin_lat=body.origin_lat,
        origin_lng=body.origin_lng,
        destination_lat=body.destination_lat,
        destination_lng=body.destination_lng,
        vehicle_type=body.vehicle_type,
        cargo_weight_kg=body.cargo_weight_kg,
        departure_time=body.departure_time,
        order_id=body.order_id,
    )
    return result
