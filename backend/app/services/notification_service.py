"""
Notification service — FCM push notifications and in-app DB notifications.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.schemas.notification import NotificationList, NotificationRead

logger = logging.getLogger(__name__)


class NotificationService:
    """Manages in-app notifications and FCM push delivery."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> dict:
        """List notifications for a user with pagination."""
        base_stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            base_stmt = base_stmt.where(Notification.is_read == False)

        # Total counts
        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = await self.db.scalar(total_stmt) or 0

        unread_stmt = select(func.count()).select_from(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            ).subquery()
        )
        unread_count = await self.db.scalar(unread_stmt) or 0

        # Fetch page
        result = await self.db.execute(
            base_stmt.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())

        return NotificationList(
            items=items,
            total=total,
            unread_count=unread_count,
            page=page,
            page_size=page_size,
        )

    async def mark_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Mark a single notification as read. Verifies ownership."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found",
            )
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        self.db.add(notification)
        await self.db.flush()

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications for a user as read. Returns count."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=now)
        )
        await self.db.flush()
        return result.rowcount

    async def delete_notification(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Delete a notification. Verifies ownership."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found",
            )
        await self.db.delete(notification)
        await self.db.flush()

    async def create_notification(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str,
        notification_type: str = "in_app",
        priority: str = "normal",
        action_url: str | None = None,
        data_payload: dict | None = None,
        send_push: bool = False,
    ) -> Notification:
        """Create an in-app notification and optionally send FCM push."""
        notification = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            data_payload=data_payload or {},
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)

        if send_push:
            await self._send_fcm_push(user_id, title, body, data_payload)

        return notification

    async def _send_fcm_push(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str,
        data_payload: dict | None = None,
    ) -> None:
        """Send a push notification via Firebase Cloud Messaging.

        This is a placeholder that logs the action. In production, it would
        look up the user's FCM device token(s) and call the Firebase API.
        """
        logger.info(
            "FCM push: user=%s title=%s body=%s",
            user_id, title, body,
        )
        # In production:
        # from firebase_admin import messaging
        # token = await get_device_token(user_id)
        # message = messaging.Message(
        #     notification=messaging.Notification(title=title, body=body),
        #     data=data_payload,
        #     token=token,
        # )
        # messaging.send(message)
