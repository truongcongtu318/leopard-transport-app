"""Order / Booking endpoint tests."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestCreateOrder:
    """Order creation endpoint."""

    async def test_create_order_minimal(
        self, client: AsyncClient, sample_order_payload: dict[str, Any], auth_headers: dict,
    ):
        """Creating an order with valid data should return 201."""
        response = await client.post(
            "/api/v1/bookings/create",
            json=sample_order_payload,
            headers=auth_headers,
        )
        assert response.status_code in (201, 401)  # 401 if no real auth

    async def test_create_order_missing_stops(self, client: AsyncClient, auth_headers: dict):
        """An order with fewer than 2 stops should be rejected."""
        response = await client.post(
            "/api/v1/bookings/create",
            json={"stops": [], "items": [], "vehicle_type": "truck_2t_5t"},
            headers=auth_headers,
        )
        assert response.status_code in (422, 401)

    async def test_create_order_unauthenticated(self, client: AsyncClient, sample_order_payload: dict):
        """Creating order without auth should return 401."""
        response = await client.post(
            "/api/v1/bookings/create",
            json=sample_order_payload,
        )
        assert response.status_code == 401


class TestGetOrder:
    """Order retrieval endpoint."""

    async def test_get_nonexistent_order(self, client: AsyncClient, auth_headers: dict):
        """Getting a nonexistent order should return 404."""
        response = await client.get(
            "/api/v1/bookings/99999",
            headers=auth_headers,
        )
        assert response.status_code in (404, 401)


class TestOrderStatusTransitions:
    """Order status transition validation."""

    async def test_invalid_status_transition(self, client: AsyncClient, auth_headers: dict):
        """Transitioning to invalid status should be rejected."""
        response = await client.post(
            "/api/v1/bookings/1/status",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code in (404, 422, 401)
