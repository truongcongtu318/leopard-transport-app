"""
ETAPrediction model — stores ML-predicted ETA results.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ETAPrediction(TimestampMixin, Base):
    __tablename__ = "eta_predictions"

    __table_args__ = (
        Index("IX_eta_predictions_order_id", "order_id"),
        Index("IX_eta_predictions_active_trip_id", "active_trip_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", name="FK_eta_predictions_order_id"),
        nullable=False,
    )
    active_trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("active_trips.id", name="FK_eta_predictions_active_trip_id"),
        nullable=True,
    )
    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str | None] = mapped_column(
        nullable=True, default="xgboost-v1"
    )
    weather_data: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )
    traffic_data: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )
    features_vector: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<ETAPrediction {self.distance_km}km "
            f"-> {self.predicted_duration_min}min "
            f"(conf: {self.confidence_score:.2f})>"
        )
