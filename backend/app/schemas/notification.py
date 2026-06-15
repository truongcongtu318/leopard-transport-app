"""
Notification schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationRead(BaseModel):
    """Notification record returned to clients."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    body: str
    notification_type: str
    priority: str
    is_read: bool
    read_at: datetime | None = None
    action_url: str | None = None
    data_payload: dict | None = None
    sent_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationRead]
    total: int
    unread_count: int
    page: int = 1
    page_size: int = 20
