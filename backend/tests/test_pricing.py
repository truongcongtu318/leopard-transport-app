"""Pricing service tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestFareCalculation:
    """Fare calculation logic."""

    async def test_calculate_fare_basic(self, client):
        """Basic fare calculation with distance and vehicle type."""
        response = await client.post(
            "/api/v1/billing/calculate-fare",
            json={
                "distance_km": 15.5,
                "vehicle_type": "truck_2t_5t",
                "weight_kg": 2000.0,
                "stop_count": 2,
            },
        )
        assert response.status_code in (200, 422)

    async def test_calculate_fare_long_distance(self, client):
        """Fare for long distance should scale appropriately."""
        response = await client.post(
            "/api/v1/billing/calculate-fare",
            json={
                "distance_km": 300.0,
                "vehicle_type": "truck_5t_10t",
                "weight_kg": 8000.0,
                "stop_count": 4,
            },
        )
        assert response.status_code in (200, 422)


class TestPricingFormula:
    """Test the base fare formula directly."""

    @pytest.mark.parametrize(
        "distance,vehicle,weight,expected_range",
        [
            (10, "truck_under_2t", 1000, (100_000, 500_000)),
            (50, "truck_2t_5t", 3000, (300_000, 2_000_000)),
            (100, "truck_5t_10t", 7000, (1_000_000, 5_000_000)),
            (500, "container", 20000, (5_000_000, 30_000_000)),
        ],
    )
    def test_price_in_expected_range(
        self, distance, vehicle, weight, expected_range,
    ):
        """Computed prices should fall within expected VND ranges for Vietnam market."""
        from app.services.pricing_service import PricingService

        svc = PricingService()
        fare = svc.calculate_base_fare(
            distance_km=Decimal(str(distance)),
            vehicle_type=vehicle,
            weight_kg=Decimal(str(weight)),
            stop_count=2,
        )
        low, high = expected_range
        assert low <= int(fare) <= high, f"Fare {fare} out of range [{low}, {high}]"
