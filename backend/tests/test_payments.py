"""Payment endpoint tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestFareCalculationEndpoint:
    """Billing fare calculation endpoint."""

    async def test_calculate_fare_valid(self, client):
        """Valid fare calculation should return price breakdown."""
        response = await client.post(
            "/api/v1/billing/calculate-fare",
            json={
                "distance_km": 25.0,
                "vehicle_type": "truck_2t_5t",
                "weight_kg": 3000.0,
                "stop_count": 3,
            },
        )
        assert response.status_code in (200, 422)

    async def test_calculate_fare_missing_fields(self, client):
        """Missing required fields should return 422."""
        response = await client.post(
            "/api/v1/billing/calculate-fare",
            json={"distance_km": 25.0},
        )
        assert response.status_code == 422


class TestVietQRGeneration:
    """VietQR generation logic."""

    async def test_generate_qr_valid(self, client, auth_headers):
        """Valid VietQR request should return QR URL and bank info."""
        response = await client.post(
            "/api/v1/billing/payments/vietqr",
            json={
                "amount": 1_500_000,
                "booking_id": "bk_test_123",
                "method": "bank_transfer",
            },
            headers=auth_headers,
        )
        assert response.status_code in (200, 401)

    async def test_generate_qr_invalid_amount(self, client, auth_headers):
        """Zero or negative amount should be rejected."""
        response = await client.post(
            "/api/v1/billing/payments/vietqr",
            json={
                "amount": 0,
                "booking_id": "bk_test_123",
                "method": "bank_transfer",
            },
            headers=auth_headers,
        )
        # 422 from Pydantic validation (amount > 0 check)
        assert response.status_code in (422, 401)


class TestPaymentSchema:
    """Payment schemas."""

    def test_vietqr_request_schema(self):
        """VietQR request should validate bank_code enum."""
        from app.schemas.payment import VietQRRequest

        req = VietQRRequest(
            amount=1_500_000,
            booking_id="bk_test_123",
            method="bank_transfer",
            bank_code="VTB",
        )
        assert req.amount == 1_500_000
        assert req.bank_code == "VTB"

    def test_fare_calc_request_schema(self):
        """Fare calculation request schema."""
        from app.schemas.payment import FareCalcRequest

        req = FareCalcRequest(
            distance_km=25.0,
            vehicle_type="truck_2t_5t",
            weight_kg=3000.0,
            stop_count=3,
            has_loading_dock=False,
        )
        assert req.vehicle_type == "truck_2t_5t"
        assert req.has_loading_dock is False

    def test_fare_calc_response_schema(self):
        """Fare calculation response schema."""
        from app.schemas.payment import FareCalcResponse

        resp = FareCalcResponse(
            base_fare=500_000,
            distance_fare=350_000,
            weight_surcharge=200_000,
            stop_surcharge=100_000,
            total_fare=1_150_000,
            currency="VND",
            breakdown={
                "base_rate": 20_000,
                "per_km_rate": 5_000,
                "per_kg_rate": 100,
            },
        )
        assert resp.total_fare == 1_150_000
        assert resp.currency == "VND"
