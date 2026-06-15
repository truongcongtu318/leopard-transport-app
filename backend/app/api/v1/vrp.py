"""
VRP optimisation endpoint.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.vrp import VRPOptimizeRequest, VRPOptimizeResponse
from app.services.vrp_service import VRPBatchOptimizationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/optimize",
    response_model=VRPOptimizeResponse,
    summary="Optimize vehicle routing for a batch of bookings",
)
async def optimize_routes(
    body: VRPOptimizeRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> VRPOptimizeResponse:
    """Run VRP solver to optimize multi-vehicle, multi-stop routing.

    Uses Google OR-Tools CVRP solver. Returns optimized routes for each vehicle.
    """
    service = VRPBatchOptimizationService(db)
    result = await service.optimize(
        vehicles=body.vehicles,
        stops=body.stops,
        depot_lat=body.depot_lat,
        depot_lng=body.depot_lng,
        solver_time_limit_s=body.solver_time_limit_s,
        priority=body.priority,
        requested_by=current_user.id,
    )
    return result
