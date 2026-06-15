"""
ActiveTrip model — tracks live trips.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ActiveTrip(TimestampMixin, Base):
    __tablename__ = "active_trips"

    __table_args__ = (
        CheckConstraint(
            "status IN ('en_route_pickup', 'at_pickup', 'en_route_delivery', "
            "'at_delivery', 'completed')",
            name="CHK_active_trips_status",
        ),
        Index("IX_active_trips_order_id", "order_id"),
        Index("IX_active_trips_driver_id", "driver_id"),
        Index("IX_active_trips_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", name="FK_active_trips_order_id"),
        unique=True,
        nullable=False,
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", name="FK_active_trips_driver_id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="en_route_pickup"
    )
    current_location: Mapped[object | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    current_stop_sequence: Mapped[int | None] = mapped_column(nullable=True)
    route_polyline: Mapped[str | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trip_metadata: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    # Relationships
    order = relationship("Order", back_populates="active_trip")
    driver = relationship("Driver", back_populates="active_trips")

    def __repr__(self) -> str:
        return f"<ActiveTrip {self.id} ({self.status})>"
