"""
Notification routes — list, mark read, delete.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.notification import NotificationList, NotificationRead
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=NotificationList, summary="List notifications")
async def list_notifications(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
) -> NotificationList:
    """List notifications for the authenticated user."""
    service = NotificationService(db)
    return await service.list_notifications(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )


@router.patch(
    "/{notification_id}/read",
    summary="Mark notification as read",
)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Mark a single notification as read."""
    service = NotificationService(db)
    await service.mark_read(notification_id, current_user.id)
    return {"status": "read"}


@router.patch(
    "/read-all",
    summary="Mark all notifications as read",
)
async def mark_all_read(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Mark all notifications for the current user as read."""
    service = NotificationService(db)
    count = await service.mark_all_read(current_user.id)
    return {"status": "read", "count": str(count)}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a notification."""
    service = NotificationService(db)
    await service.delete_notification(notification_id, current_user.id)
