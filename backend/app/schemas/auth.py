"""
Authentication schemas: OTP request/verify, Google sign-in, token response.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    """Request to send an OTP to a phone number."""

    phone_number: str = Field(
        ...,
        pattern=r"^\+84\d{9,10}$",
        examples=["+84912345678"],
        description="Vietnamese phone number in E.164 format",
    )


class OTPVerify(BaseModel):
    """Verify an OTP code and receive JWT tokens."""

    phone_number: str = Field(
        ...,
        pattern=r"^\+84\d{9,10}$",
    )
    otp_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit OTP code",
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="Full name for new user registration",
    )


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Seconds until token expires")
    user_id: str = Field(..., description="UUID of authenticated user")
    role: str = Field(..., description="User role")


class GoogleAuthRequest(BaseModel):
    """Google sign-in with Firebase ID token."""

    id_token: str = Field(
        ...,
        description="Firebase ID token from Google Sign-In",
    )
