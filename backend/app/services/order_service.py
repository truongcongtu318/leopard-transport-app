"""
Order service — create orders, validate stops, manage status transitions, bidding.
"""

from __future__ import annotations

import logging
import random
import string
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.notification import OrderStatusLog
from app.models.order import Order, OrderBid, OrderItem, OrderStop
from app.models.user import User
from app.schemas.bid import BidCreate
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["pending", "cancelled"],
    "pending": ["bidding", "accepted", "cancelled"],
    "bidding": ["accepted", "cancelled"],
    "accepted": ["pickup_in_progress", "cancelled"],
    "pickup_in_progress": ["in_transit", "cancelled"],
    "in_transit": ["delivered"],
    "delivered": ["completed", "disputed"],
    "completed": [],
    "cancelled": [],
    "disputed": ["completed"],
}


class OrderService:
    """Business logic for order lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _generate_tracking_code() -> str:
        """Generate a 12-char alphanumeric tracking code."""
        prefix = "LP"
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return prefix + suffix

    async def create_order(
        self,
        shipper_id: uuid.UUID,
        data: OrderCreate,
    ) -> Order:
        """Create a new order with stops and items."""
        # Validate at least 1 pickup and 1 dropoff
        pickup_count = sum(1 for s in data.stops if s.stop_type == "pickup")
        dropoff_count = sum(1 for s in data.stops if s.stop_type == "dropoff")
        if pickup_count < 1 or dropoff_count < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must have at least one pickup and one dropoff stop",
            )

        tracking_code = self._generate_tracking_code()

        order = Order(
            shipper_id=shipper_id,
            tracking_code=tracking_code,
            status="pending",
            cargo_type=data.cargo_type,
            total_weight_kg=data.total_weight_kg,
            total_volume_cbm=data.total_volume_cbm,
            cargo_value=data.cargo_value,
            cargo_description=data.cargo_description,
            special_instructions=data.special_instructions,
            pickup_deadline=data.pickup_deadline,
            delivery_deadline=data.delivery_deadline,
        )
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)

        # Create stops
        for stop_data in data.stops:
            stop = OrderStop(
                order_id=order.id,
                stop_type=stop_data.stop_type,
                sequence=stop_data.sequence,
                address=stop_data.address,
                location=f"SRID=4326;POINT({stop_data.longitude} {stop_data.latitude})",
                contact_name=stop_data.contact_name,
                contact_phone=stop_data.contact_phone,
                notes=stop_data.notes,
                planned_arrival=stop_data.planned_arrival,
            )
            self.db.add(stop)

        # Create items
        for item_data in data.items:
            item = OrderItem(
                order_id=order.id,
                item_name=item_data.item_name,
                quantity=item_data.quantity,
                weight_kg=item_data.weight_kg,
                volume_cbm=item_data.volume_cbm,
                unit_value=item_data.unit_value,
                package_type=item_data.package_type,
                is_fragile=int(item_data.is_fragile),
            )
            self.db.add(item)

        await self.db.flush()

        # Create initial status log
        status_log = OrderStatusLog(
            order_id=order.id,
            old_status=None,
            new_status="pending",
            changed_by=shipper_id,
            reason="Order created",
        )
        self.db.add(status_log)
        await self.db.flush()
        await self.db.refresh(order)

        logger.info("Order %s created by shipper %s", tracking_code, shipper_id)
        return order

    async def get_order_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Fetch an order by ID with stops and items."""
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_orders(
        self,
        user_id: uuid.UUID,
        role: str,
        status_filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Order]:
        """List orders for a user filtered by role."""
        stmt = select(Order)
        if role == "shipper":
            stmt = stmt.where(Order.shipper_id == user_id)
        elif role == "driver":
            # Find driver record
            driver_result = await self.db.execute(
                select(Driver).where(Driver.user_id == user_id)
            )
            driver = driver_result.scalar_one_or_none()
            if driver:
                stmt = stmt.where(Order.driver_id == driver.id)
            else:
                return []
        # Admin / fleet_owner: show all

        if status_filter:
            stmt = stmt.where(Order.status == status_filter)

        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        order_id: uuid.UUID,
        new_status: str,
        changed_by: uuid.UUID,
        changed_by_role: str,
        reason: str | None = None,
    ) -> Order:
        """Transition an order to a new status."""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = order.status
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from '{current_status}' to '{new_status}'. "
                f"Allowed: {', '.join(allowed)}",
            )

        order.status = new_status

        # Update timestamps based on status
        now = datetime.now(timezone.utc)
        if new_status == "pickup_in_progress":
            order.actual_pickup_at = now
        elif new_status == "delivered":
            order.actual_delivery_at = now
        elif new_status == "cancelled":
            order.cancelled_at = now
            order.cancel_reason = reason

        self.db.add(order)

        # Status log
        log = OrderStatusLog(
            order_id=order.id,
            old_status=current_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(order)

        logger.info(
            "Order %s status: %s -> %s (by %s)",
            order.tracking_code, current_status, new_status, changed_by,
        )
        return order

    async def place_bid(
        self,
        order_id: uuid.UUID,
        driver_user: User,
        data: BidCreate,
    ) -> OrderBid:
        """Driver places a bid on an order."""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status not in ("pending", "bidding"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not accepting bids",
            )

        # Get driver record
        driver_result = await self.db.execute(
            select(Driver).where(Driver.user_id == driver_user.id)
        )
        driver = driver_result.scalar_one_or_none()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        if driver.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Driver is not approved",
            )

        # Check for existing bid
        existing = await self.db.execute(
            select(OrderBid).where(
                OrderBid.order_id == order_id,
                OrderBid.driver_id == driver.id,
                OrderBid.status == "pending",
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a pending bid on this order",
            )

        bid = OrderBid(
            order_id=order_id,
            driver_id=driver.id,
            bid_amount=data.bid_amount,
            estimated_duration_min=data.estimated_duration_min,
            bid_message=data.bid_message,
            status="pending",
        )
        self.db.add(bid)

        # Update order to bidding status
        if order.status == "pending":
            order.status = "bidding"
            self.db.add(order)

        await self.db.flush()
        await self.db.refresh(bid)
        return bid

    async def list_bids(self, order_id: uuid.UUID) -> list[OrderBid]:
        """List all bids for an order."""
        result = await self.db.execute(
            select(OrderBid)
            .where(OrderBid.order_id == order_id)
            .order_by(OrderBid.bid_amount.asc())
        )
        return list(result.scalars().all())

    async def accept_bid(
        self,
        order_id: uuid.UUID,
        bid_id: uuid.UUID,
        shipper_id: uuid.UUID,
    ) -> OrderBid:
        """Shipper accepts a bid on their order."""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.shipper_id != shipper_id:
            raise HTTPException(status_code=403, detail="Only the shipper can accept bids")
        if order.status not in ("pending", "bidding"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not in bidding state",
            )

        # Find the bid
        result = await self.db.execute(
            select(OrderBid).where(
                OrderBid.id == bid_id,
                OrderBid.order_id == order_id,
            )
        )
        bid = result.scalar_one_or_none()
        if not bid:
            raise HTTPException(status_code=404, detail="Bid not found")

        # Accept this bid
        now = datetime.now(timezone.utc)
        bid.status = "accepted"
        bid.accepted_at = now
        self.db.add(bid)

        # Reject other bids
        other_result = await self.db.execute(
            select(OrderBid).where(
                OrderBid.order_id == order_id,
                OrderBid.id != bid_id,
                OrderBid.status == "pending",
            )
        )
        for other_bid in other_result.scalars().all():
            other_bid.status = "rejected"
            other_bid.rejected_at = now
            self.db.add(other_bid)

        # Update order
        order.status = "accepted"
        order.driver_id = bid.driver_id
        order.final_fare = bid.bid_amount
        self.db.add(order)

        await self.db.flush()
        await self.db.refresh(bid)

        logger.info(
            "Bid %s accepted for order %s", bid_id, order.tracking_code,
        )
        return bid
