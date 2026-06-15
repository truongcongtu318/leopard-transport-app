"""
Driver and DriverDocument models.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'suspended', 'rejected')",
            name="CHK_drivers_status",
        ),
        CheckConstraint(
            "license_class IN ('B2', 'C', 'D', 'E', 'FC')",
            name="CHK_drivers_license_class",
        ),
        Index("IX_drivers_user_id", "user_id"),
        Index("IX_drivers_status", "status"),
        Index("IX_drivers_business_id", "business_id"),
        Index(
            "IX_drivers_current_location",
            "current_location",
            postgresql_using="gist",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_drivers_user_id"),
        unique=True,
        nullable=False,
    )
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", name="FK_drivers_business_id"),
        nullable=True,
    )
    license_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    license_class: Mapped[str] = mapped_column(String(5), nullable=False)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    id_card_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    current_location: Mapped[object | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    is_online: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_busy: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    rating: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("5.0")
    )
    total_trips: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", name="FK_drivers_vehicle_id"),
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="driver", lazy="joined")
    vehicle = relationship("Vehicle", back_populates="driver", lazy="selectin")
    documents = relationship("DriverDocument", back_populates="driver", lazy="selectin")
    business = relationship("Business", back_populates="drivers", lazy="noload")
    active_trips = relationship("ActiveTrip", back_populates="driver", lazy="noload")
    bids = relationship("OrderBid", back_populates="driver", lazy="noload")

    def __repr__(self) -> str:
        return f"<Driver {self.license_number} ({self.status})>"


class DriverDocument(TimestampMixin, Base):
    __tablename__ = "driver_documents"

    __table_args__ = (
        CheckConstraint(
            "document_type IN ('license_front', 'license_back', 'id_card_front', "
            "'id_card_back', 'vehicle_registration', 'insurance')",
            name="CHK_driver_documents_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="CHK_driver_documents_status",
        ),
        Index("IX_driver_documents_driver_id", "driver_id"),
        Index("IX_driver_documents_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", name="FK_driver_documents_driver_id"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_driver_documents_reviewed_by"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    driver = relationship("Driver", back_populates="documents")
    reviewer = relationship("User", foreign_keys=[reviewed_by], lazy="noload")

    def __repr__(self) -> str:
        return f"<DriverDocument {self.document_type} ({self.status})>"
