"""Notification dispatch worker — FCM push via Celery."""

from __future__ import annotations

import logging
from typing import Any

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="notifications.send_push",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def send_push_notification(
    self,
    user_id: int,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send FCM push notification to a user's devices.

    Args:
        user_id: Target user ID.
        title: Notification title.
        body: Notification body text.
        data: Optional payload data.

    Returns:
        Dict with send result per device token.
    """
    from firebase_admin import messaging  # noqa: C0415

    try:
        # In production, query user's FCM tokens from DB
        # For now, log the intent
        logger.info(
            "Sending push to user=%d title=%r body=%r",
            user_id, title, body,
        )

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            topic=f"user_{user_id}",
        )
        response = messaging.send(message)
        logger.info("FCM response: %s", response)
        return {"success": True, "message_id": response}

    except Exception as exc:
        logger.exception("FCM push failed for user=%d", user_id)
        raise self.retry(exc=exc)


@celery_app.task(name="notifications.send_bulk")
def send_bulk_notification(
    user_ids: list[int],
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send push notification to multiple users."""
    results = {}
    for uid in user_ids:
        try:
            send_push_notification.delay(uid, title, body, data)
            results[uid] = "queued"
        except Exception:
            logger.exception("Failed to queue push for user=%d", uid)
            results[uid] = "failed"
    return results
