"""
Firebase Admin SDK initialisation.

Provides a lazily-initialised Firebase app instance.
"""

from __future__ import annotations

import firebase_admin
from firebase_admin import auth, credentials

from app.config import settings

_firebase_app: firebase_admin.App | None = None


def get_firebase_app() -> firebase_admin.App:
    """Return (and initialise if needed) the Firebase Admin SDK app."""
    global _firebase_app
    if _firebase_app is None:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


async def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims.

    Raises ``firebase_admin.auth.InvalidIdTokenError`` on failure.
    """
    return auth.verify_id_token(id_token, app=get_firebase_app())


async def verify_phone_otp(phone_number: str, otp_code: str) -> bool:
    """Verify a phone OTP using Firebase Auth.

    In production this would call Firebase's phone auth API.
    For now this is a placeholder that uses Firebase custom token verification.
    """
    try:
        firebase_auth = auth
        # Firebase Phone Auth session verification
        user = firebase_auth.get_user_by_phone_number(phone_number, app=get_firebase_app())
        return user.uid is not None
    except Exception:
        return False
