"""
WebSocket endpoint for real-time GPS tracking.
"""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis
from app.core.security import decode_access_token
from app.services.tracking_service import TrackingService

logger = logging.getLogger(__name__)

router = APIRouter()
tracking_service = TrackingService()


@router.websocket("/ws")
async def tracking_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None, alias="token"),
    role: str = Query(default="shipper", alias="role"),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time GPS tracking.

    - Drivers send ``LocationUpdate`` JSON messages.
    - Shippers receive ``TrackingEvent`` broadcasts for their active orders.

    Authentication via query parameter ``?token=JWT``.
    """
    user_id: uuid.UUID | None = None

    if token:
        payload = decode_access_token(token)
        if payload:
            try:
                user_id = uuid.UUID(payload.get("sub", ""))
            except ValueError:
                pass

    await websocket.accept()

    if user_id is None:
        await websocket.send_json({"error": "Invalid or missing authentication token"})
        await websocket.close()
        return

    # Register the connection
    await tracking_service.connect(websocket, user_id, role)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if role == "driver":
                # Driver sending a location update
                await tracking_service.handle_location_update(user_id, message, db)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user %s", user_id)
    except Exception:
        logger.exception("WebSocket error for user %s")
    finally:
        await tracking_service.disconnect(websocket, user_id)
