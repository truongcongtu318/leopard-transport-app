"""VRP / Route Optimization tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestVRPSchema:
    """VRP request/response schemas."""

    def test_vrp_request_schema(self):
        """VRP request should accept valid stops and vehicles."""
        from app.schemas.vrp import VRPOptimizeRequest, StopDef, VehicleDef

        req = VRPOptimizeRequest(
            stops=[
                StopDef(
                    id="stop_0",
                    latitude=10.7769,
                    longitude=106.7009,
                    stop_type="depot",
                    demand_kg=0,
                ),
                StopDef(
                    id="stop_1",
                    latitude=10.7689,
                    longitude=106.7012,
                    stop_type="pickup",
                    demand_kg=1500,
                    time_window_start="08:00",
                    time_window_end="17:00",
                ),
                StopDef(
                    id="stop_2",
                    latitude=10.7900,
                    longitude=106.7200,
                    stop_type="dropoff",
                    demand_kg=1500,
                ),
            ],
            vehicles=[
                VehicleDef(
                    id="v_1",
                    capacity_kg=5000,
                    start_lat=10.7769,
                    start_lng=106.7009,
                ),
            ],
            max_detour_km=5.0,
        )
        assert len(req.stops) == 3
        assert req.vehicles[0].capacity_kg == 5000

    def test_vrp_invalid_stop_count(self):
        """VRP with fewer than 2 stops should fail validation."""
        from app.schemas.vrp import VRPOptimizeRequest, StopDef, VehicleDef

        import pydantic

        with pytest.raises(pydantic.ValidationError):
            VRPOptimizeRequest(
                stops=[
                    StopDef(
                        id="stop_0",
                        latitude=10.7769,
                        longitude=106.7009,
                        stop_type="depot",
                        demand_kg=0,
                    ),
                ],
                vehicles=[
                    VehicleDef(
                        id="v_1",
                        capacity_kg=5000,
                        start_lat=10.7769,
                        start_lng=106.7009,
                    ),
                ],
            )

    def test_vrp_response_schema(self):
        """VRP response should contain ordered routes."""
        from app.schemas.vrp import VRPOptimizeResponse, VehicleRoute, StopVisit

        resp = VRPOptimizeResponse(
            routes=[
                VehicleRoute(
                    vehicle_id="v_1",
                    stops=[
                        StopVisit(stop_id="stop_0", arrival_min=0, departure_min=0),
                        StopVisit(stop_id="stop_1", arrival_min=5, departure_min=10),
                        StopVisit(stop_id="stop_2", arrival_min=18, departure_min=23),
                    ],
                    total_distance_km=8.5,
                    total_duration_min=23,
                    total_load_kg=1500,
                ),
            ],
            total_distance_km=8.5,
            solver_status="optimal",
            solve_time_ms=42,
        )
        assert resp.solver_status == "optimal"
        assert len(resp.routes) == 1
        assert resp.routes[0].stops[1].arrival_min == 5


class TestRouteOptimizationModel:
    """Route optimization database model."""

    def test_route_optimization_row(self):
        """Route optimization model should accept valid data."""
        from app.models.vrp import RouteOptimization
        from datetime import datetime, timezone

        row = RouteOptimization(
            driver_id=1,
            order_id=1,
            suggested_orders=[{
                "order_id": 2,
                "stop_id": 3,
                "lat": 10.7689,
                "lng": 106.7012,
                "weight": 1000,
                "detour_km": 2.3,
            }],
            total_detour_km=2.3,
            total_extra_earnings=150_000,
            solve_time_ms=85,
            status="pending",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
        )
        assert row.status == "pending"
        assert row.suggested_orders[0]["order_id"] == 2
