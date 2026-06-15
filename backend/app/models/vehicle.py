"""
Vehicle model.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    __table_args__ = (
        CheckConstraint(
            "vehicle_type IN ('three_wheeler', 'truck_under_2t', 'truck_2t_5t', "
            "'truck_5t_10t', 'truck_over_10t', 'container')",
            name="CHK_vehicles_vehicle_type",
        ),
        CheckConstraint(
            "status IN ('active', 'maintenance', 'retired')",
            name="CHK_vehicles_status",
        ),
        Index("IX_vehicles_license_plate", "license_plate"),
        Index("IX_vehicles_vehicle_type", "vehicle_type"),
        Index("IX_vehicles_owner_id", "owner_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    license_plate: Mapped[str] = mapped_column(
        String(15), unique=True, nullable=False
    )
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    year_of_manufacture: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_payload_kg: Mapped[float] = mapped_column(Float, nullable=False)
    max_volume_cbm: Mapped[float | None] = mapped_column(Float, nullable=True)
    length_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="active"
    )
    images: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=True
    )
    registration_expiry: Mapped[str | None] = mapped_column(String(10), nullable=True)
    insurance_expiry: Mapped[str | None] = mapped_column(String(10), nullable=True)
    features: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=True
    )

    # Relationships
    driver = relationship("Driver", back_populates="vehicle", uselist=False, lazy="noload")

    def __repr__(self) -> str:
        return f"<Vehicle {self.license_plate} ({self.vehicle_type})>"
