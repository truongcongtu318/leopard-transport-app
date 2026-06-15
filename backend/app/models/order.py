"""
Order, OrderStop, OrderItem, and OrderBid models.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending', 'bidding', 'accepted', "
            "'pickup_in_progress', 'in_transit', 'delivered', "
            "'completed', 'cancelled', 'disputed')",
            name="CHK_orders_status",
        ),
        CheckConstraint(
            "cargo_type IN ('general', 'fragile', 'perishable', 'dangerous', 'oversized')",
            name="CHK_orders_cargo_type",
        ),
        Index("IX_orders_shipper_id", "shipper_id"),
        Index("IX_orders_driver_id", "driver_id"),
        Index("IX_orders_status", "status"),
        Index("IX_orders_tracking_code", "tracking_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    shipper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_orders_shipper_id"),
        nullable=False,
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", name="FK_orders_driver_id"),
        nullable=True,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", name="FK_orders_vehicle_id"),
        nullable=True,
    )
    tracking_code: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="draft"
    )
    cargo_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="general"
    )
    total_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    total_volume_cbm: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    cargo_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    cargo_description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    special_instructions: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    estimated_distance_km: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    estimated_duration_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    base_fare: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_fare: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="VND"
    )
    pickup_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivery_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_pickup_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_delivery_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    shipper = relationship("User", back_populates="orders", foreign_keys=[shipper_id], lazy="noload")
    driver = relationship("Driver", foreign_keys=[driver_id], lazy="noload")
    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id], lazy="noload")
    stops = relationship("OrderStop", back_populates="order", lazy="selectin")
    items = relationship("OrderItem", back_populates="order", lazy="selectin")
    bids = relationship("OrderBid", back_populates="order", lazy="selectin")
    payments = relationship("Payment", back_populates="order", lazy="selectin")
    active_trip = relationship("ActiveTrip", back_populates="order", uselist=False, lazy="noload")
    status_logs = relationship("OrderStatusLog", back_populates="order", lazy="noload")

    def __repr__(self) -> str:
        return f"<Order {self.tracking_code} ({self.status})>"


class OrderStop(TimestampMixin, Base):
    __tablename__ = "order_stops"

    __table_args__ = (
        CheckConstraint(
            "stop_type IN ('pickup', 'dropoff', 'waypoint')",
            name="CHK_order_stops_stop_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'arrived', 'departed', 'completed', 'skipped')",
            name="CHK_order_stops_status",
        ),
        Index("IX_order_stops_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", name="FK_order_stops_order_id"),
        nullable=False,
    )
    stop_type: Mapped[str] = mapped_column(String(20), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    contact_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(15), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    planned_arrival: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_arrival: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_departure: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    location_metadata: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    # Relationships
    order = relationship("Order", back_populates="stops")

    def __repr__(self) -> str:
        return f"<OrderStop {self.stop_type} #{self.sequence}>"


class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"

    __table_args__ = (
        Index("IX_order_items_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", name="FK_order_items_order_id"),
        nullable=False,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_cbm: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    package_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_fragile: Mapped[bool] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    item_metadata: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    # Relationships
    order = relationship("Order", back_populates="items")

    def __repr__(self) -> str:
        return f"<OrderItem {self.item_name}>"


class OrderBid(TimestampMixin, Base):
    __tablename__ = "order_bids"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'withdrawn')",
            name="CHK_order_bids_status",
        ),
        Index("IX_order_bids_order_id", "order_id"),
        Index("IX_order_bids_driver_id", "driver_id"),
        Index("IX_order_bids_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", name="FK_order_bids_order_id"),
        nullable=False,
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", name="FK_order_bids_driver_id"),
        nullable=False,
    )
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    bid_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    order = relationship("Order", back_populates="bids")
    driver = relationship("Driver", back_populates="bids")

    def __repr__(self) -> str:
        return f"<OrderBid {self.bid_amount} ({self.status})>"
