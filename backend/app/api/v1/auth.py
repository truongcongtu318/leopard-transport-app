"""
Authentication routes — phone OTP and Google Sign-In.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.auth import (
    GoogleAuthRequest,
    OTPRequest,
    OTPVerify,
    TokenResponse,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/phone/otp-request",
    status_code=status.HTTP_200_OK,
    summary="Request OTP for phone authentication",
)
async def request_otp(
    body: OTPRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Send a 6-digit OTP to the provided Vietnamese phone number."""
    service = AuthService(db)
    await service.request_otp(body.phone_number)
    return {"message": "OTP sent successfully", "phone_number": body.phone_number}


@router.post(
    "/phone/otp-verify",
    response_model=TokenResponse,
    summary="Verify phone OTP and receive JWT",
)
async def verify_otp(
    body: OTPVerify,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Verify OTP code. Creates a new user if first login."""
    service = AuthService(db)
    token_response = await service.verify_otp(
        phone_number=body.phone_number,
        otp_code=body.otp_code,
        full_name=body.full_name,
    )
    return token_response


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Authenticate via Google (Firebase)",
)
async def google_auth(
    body: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Verify Firebase ID token from Google Sign-In, issue a JWT."""
    service = AuthService(db)
    token_response = await service.google_sign_in(body.id_token)
    return token_response
