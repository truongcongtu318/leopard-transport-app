"""ETA prediction tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestETASchema:
    """ETA request/response schemas."""

    def test_eta_request_schema(self):
        """ETA request with valid data should parse correctly."""
        from app.schemas.eta import ETAPredictRequest

        req = ETAPredictRequest(
            origin_lat=10.7769,
            origin_lng=106.7009,
            dest_lat=10.8500,
            dest_lng=106.7700,
            vehicle_type="truck_2t_5t",
        )
        assert req.origin_lat == 10.7769
        assert req.vehicle_type == "truck_2t_5t"

    def test_eta_response_schema(self):
        """ETA response should include required fields."""
        from app.schemas.eta import ETAPredictResponse

        resp = ETAPredictResponse(
            predicted_minutes=35.5,
            distance_km=18.2,
            confidence_low=28.0,
            confidence_high=42.0,
        )
        assert resp.predicted_minutes == 35.5
        assert resp.confidence_low <= resp.confidence_high


class TestETAService:
    """ETA service haversine fallback."""

    def test_haversine_fallback(self):
        """Haversine fallback should return reasonable estimates."""
        from app.services.eta_service import ETAService

        svc = ETAService()
        result = svc._haversine_fallback(
            origin_lat=10.7769,
            origin_lng=106.7009,
            dest_lat=10.8500,
            dest_lng=106.7700,
        )
        # The distance between these two points is ~11km
        assert 8 < result["distance_km"] < 15
        # Assuming ~35 km/h average city speed
        assert 15 < result["predicted_minutes"] < 40


class TestETAModel:
    """ETA prediction database model."""

    def test_eta_prediction_row(self):
        """An ETA prediction row should accept valid data."""
        from app.models.eta import ETAPrediction
        from datetime import datetime, timezone

        row = ETAPrediction(
            origin_lat=10.7769,
            origin_lng=106.7009,
            dest_lat=10.8500,
            dest_lng=106.7700,
            distance_km=11.5,
            predicted_minutes=25.0,
            model_version="v1.0.0",
            features={
                "hour": 14,
                "day_of_week": 3,
                "is_rain": False,
            },
            created_at=datetime.now(timezone.utc),
        )
        assert row.model_version == "v1.0.0"
        assert row.features["hour"] == 14
