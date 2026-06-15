"""
RouteOptimization model — stores VRP solver results.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RouteOptimization(TimestampMixin, Base):
    __tablename__ = "route_optimizations"

    __table_args__ = (
        CheckConstraint(
            "solver_status IN ('optimal', 'feasible', 'infeasible', 'timeout', 'error')",
            name="CHK_route_optimizations_solver_status",
        ),
        Index("IX_route_optimizations_requested_by", "requested_by"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    input_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )
    result_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    solver_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="feasible"
    )
    total_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_vehicles_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_stops_optimized: Mapped[int | None] = mapped_column(Integer, nullable=True)
    solver_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RouteOptimization {self.id} "
            f"({self.solver_status}, {self.num_stops_optimized} stops)>"
        )
