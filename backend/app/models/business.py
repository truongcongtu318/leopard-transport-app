"""
Business, BusinessContract, and BusinessDriver models.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
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


class Business(TimestampMixin, Base):
    __tablename__ = "businesses"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'suspended', 'closed')",
            name="CHK_businesses_status",
        ),
        Index("IX_businesses_owner_id", "owner_id"),
        Index("IX_businesses_status", "status"),
        Index("IX_businesses_tax_code", "tax_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_businesses_owner_id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    province_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    district_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    fleet_size: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    driver_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    rating: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("5.0")
    )
    settings_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], lazy="noload")
    drivers = relationship("Driver", back_populates="business", lazy="selectin")
    contracts = relationship("BusinessContract", back_populates="business", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Business {self.name} ({self.status})>"


class BusinessContract(TimestampMixin, Base):
    __tablename__ = "business_contracts"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'expired', 'terminated')",
            name="CHK_business_contracts_status",
        ),
        Index("IX_business_contracts_business_id", "business_id"),
        Index("IX_business_contracts_shipper_id", "shipper_id"),
        Index("IX_business_contracts_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", name="FK_business_contracts_business_id"),
        nullable=False,
    )
    shipper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="FK_business_contracts_shipper_id"),
        nullable=False,
    )
    contract_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    base_rate: Mapped[float] = mapped_column(Float, nullable=False)
    rate_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    rate_per_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_charge: Mapped[float] = mapped_column(Float, nullable=False)
    payment_terms_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("30")
    )
    contract_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    # Relationships
    business = relationship("Business", back_populates="contracts")
    shipper = relationship("User", foreign_keys=[shipper_id], lazy="noload")
    business_drivers = relationship("BusinessDriver", back_populates="contract", lazy="selectin")

    def __repr__(self) -> str:
        return f"<BusinessContract {self.contract_name} ({self.status})>"


class BusinessDriver(TimestampMixin, Base):
    __tablename__ = "business_drivers"

    __table_args__ = (
        CheckConstraint(
            "status IN ('assigned', 'unassigned')",
            name="CHK_business_drivers_status",
        ),
        Index("IX_business_drivers_contract_id", "contract_id"),
        Index("IX_business_drivers_driver_id", "driver_id"),
        Index("IX_business_drivers_vehicle_id", "vehicle_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_contracts.id", name="FK_business_drivers_contract_id"),
        nullable=False,
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", name="FK_business_drivers_driver_id"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", name="FK_business_drivers_vehicle_id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="assigned"
    )

    # Relationships
    contract = relationship("BusinessContract", back_populates="business_drivers")
    driver = relationship("Driver", foreign_keys=[driver_id], lazy="noload")
    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id], lazy="noload")

    def __repr__(self) -> str:
        return f"<BusinessDriver {self.id} ({self.status})>"
