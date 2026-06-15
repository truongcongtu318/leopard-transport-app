"""
Authentication service — Firebase verification, JWT issuance, OTP flow.
"""

from __future__ import annotations

import logging
import random
import string
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.firebase import verify_firebase_token, verify_phone_otp
from app.core.redis import redis_client
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 300  # 5 minutes
OTP_KEY_PREFIX = "otp:"


class AuthService:
    """Handles authentication flows: phone OTP, Google/Firebase sign-in."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def request_otp(self, phone_number: str) -> None:
        """Generate a 6-digit OTP and store it in Redis.

        In production, this would also trigger an SMS via a provider.
        """
        # Rate limiting
        rate_key = f"otp_rate:{phone_number}"
        current = await redis_client.get(rate_key)
        if current and int(current) >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please wait.",
            )

        # Generate OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        otp_key = f"{OTP_KEY_PREFIX}{phone_number}"
        await redis_client.set(otp_key, otp_code, ex=OTP_TTL_SECONDS)

        # Rate limit tracking
        pipe = redis_client.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, OTP_TTL_SECONDS)
        await pipe.execute()

        logger.info("OTP generated for %s (dev mode: %s)", phone_number, otp_code)

    async def verify_otp(
        self,
        phone_number: str,
        otp_code: str,
        full_name: str | None = None,
    ) -> TokenResponse:
        """Verify OTP and issue a JWT. Creates new user if first login."""
        otp_key = f"{OTP_KEY_PREFIX}{phone_number}"
        stored_otp = await redis_client.get(otp_key)

        if stored_otp is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired or not requested",
            )
        if stored_otp != otp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code",
            )

        # Delete used OTP
        await redis_client.delete(otp_key)

        # Find or create user
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # New user registration
            if not full_name:
                full_name = f"User_{phone_number[-4:]}"
            user = User(
                phone_number=phone_number,
                full_name=full_name,
                role="shipper",
                auth_provider="phone",
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
            logger.info("Created new user %s via phone OTP", user.id)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        self.db.add(user)
        await self.db.flush()

        return self._issue_token(user)

    async def google_sign_in(self, id_token: str) -> TokenResponse:
        """Verify Firebase ID token from Google Sign-In and issue a JWT."""
        try:
            claims = await verify_firebase_token(id_token)
        except Exception as exc:
            logger.warning("Firebase token verification failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase ID token",
            )

        firebase_uid = claims.get("uid") or claims.get("sub")
        email = claims.get("email")
        name = claims.get("name", "")
        picture = claims.get("picture")

        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Firebase token missing UID",
            )

        # Find by firebase_uid or email
        result = await self.db.execute(
            select(User).where(
                (User.firebase_uid == firebase_uid) | (User.email == email)
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                full_name=name or f"User_{firebase_uid[:6]}",
                avatar_url=picture,
                role="shipper",
                auth_provider="google",
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
            logger.info("Created new user %s via Google Sign-In", user.id)
        else:
            # Update firebase_uid if not set
            if not user.firebase_uid:
                user.firebase_uid = firebase_uid
            user.last_login_at = datetime.now(timezone.utc)
            self.db.add(user)
            await self.db.flush()

        return self._issue_token(user)

    def _issue_token(self, user: User) -> TokenResponse:
        """Create JWT access token from a User instance."""
        token_data = {
            "sub": str(user.id),
            "role": user.role,
        }
        access_token = create_access_token(data=token_data)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
            user_id=str(user.id),
            role=user.role,
        )
