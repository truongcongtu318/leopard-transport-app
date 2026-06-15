"""
Bidding routes — drivers bid on orders, shippers accept bids.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.bid import BidAccept, BidCreate, BidRead
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{order_id}/bids",
    response_model=BidRead,
    status_code=status.HTTP_201_CREATED,
    summary="Place a bid on an order",
)
async def create_bid(
    order_id: uuid.UUID,
    body: BidCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BidRead:
    """Driver places a bid on an order in bidding status."""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can place bids")
    service = OrderService(db)
    bid = await service.place_bid(
        order_id=order_id,
        driver_user=current_user,
        data=body,
    )
    return bid


@router.get(
    "/{order_id}/bids",
    response_model=list[BidRead],
    summary="List bids for an order",
)
async def list_bids(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[BidRead]:
    """List all bids for a specific order."""
    service = OrderService(db)
    bids = await service.list_bids(order_id)
    return bids


@router.post(
    "/{order_id}/bids/accept",
    response_model=BidRead,
    summary="Accept a bid",
)
async def accept_bid(
    order_id: uuid.UUID,
    body: BidAccept,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BidRead:
    """Shipper accepts a bid on their order."""
    service = OrderService(db)
    bid = await service.accept_bid(
        order_id=order_id,
        bid_id=body.bid_id,
        shipper_id=current_user.id,
    )
    return bid
