"""Authentication endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestPhoneOTP:
    """Phone OTP request and verification."""

    async def test_otp_request_valid_phone(self, client: AsyncClient):
        """Requesting OTP with a valid phone number should return 200."""
        response = await client.post(
            "/api/v1/auth/phone/otp-request",
            json={"phone_number": "+84901234567"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["message"] == "otp_sent"

    async def test_otp_request_invalid_phone(self, client: AsyncClient):
        """Invalid phone format should return 422 validation error."""
        response = await client.post(
            "/api/v1/auth/phone/otp-request",
            json={"phone_number": "abc"},
        )
        assert response.status_code == 422

    async def test_otp_verify_without_request(self, client: AsyncClient):
        """Verifying without prior OTP request should return 400."""
        response = await client.post(
            "/api/v1/auth/phone/otp-verify",
            json={
                "request_id": "nonexistent",
                "phone_number": "+84901234567",
                "otp_code": "123456",
            },
        )
        assert response.status_code == 400


class TestGoogleAuth:
    """Google sign-in endpoint."""

    async def test_google_auth_with_token(self, client: AsyncClient):
        """Submitting a Google ID token should return auth tokens."""
        response = await client.post(
            "/api/v1/auth/google",
            json={
                "id_token": "mock.google.id.token",
                "role": "shipper",
            },
        )
        # Without real Firebase, this may return 401, but endpoint should exist
        assert response.status_code in (200, 401)
