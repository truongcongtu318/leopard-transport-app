"""
Order routes — create, read, list, update status.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.order import (
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order (booking)",
)
async def create_order(
    body: OrderCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """Create a new freight transport order."""
    service = OrderService(db)
    order = await service.create_order(
        shipper_id=current_user.id,
        data=body,
    )
    return order


@router.get("/", response_model=list[OrderRead], summary="List user's orders")
async def list_orders(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[OrderRead]:
    """List orders for the current user, optionally filtered by status."""
    service = OrderService(db)
    orders = await service.list_orders(
        user_id=current_user.id,
        role=current_user.role,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return orders


@router.get("/{order_id}", response_model=OrderRead, summary="Get order details")
async def get_order(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """Get full details for a specific order."""
    service = OrderService(db)
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Basic ownership check
    if (
        order.shipper_id != current_user.id
        and order.driver_id != current_user.id
        and current_user.role not in ("admin", "fleet_owner")
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Update order status",
)
async def update_order_status(
    order_id: uuid.UUID,
    body: OrderStatusUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """Update an order's status (driver / admin / shipper action)."""
    service = OrderService(db)
    order = await service.update_status(
        order_id=order_id,
        new_status=body.status,
        changed_by=current_user.id,
        changed_by_role=current_user.role,
        reason=body.reason,
    )
    return order
