"""
Tracking service — WebSocket connection manager, location broadcast via Redis PubSub.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import publish, redis_client

logger = logging.getLogger(__name__)


class TrackingService:
    """Manages WebSocket connections and location broadcasts for real-time tracking."""

    def __init__(self) -> None:
        # user_id -> list of websockets
        self._active_connections: dict[uuid.UUID, list[WebSocket]] = {}
        # order_id -> set of subscriber user_ids
        self._order_subscribers: dict[uuid.UUID, set[uuid.UUID]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: uuid.UUID,
        role: str,
    ) -> None:
        """Register a new WebSocket connection."""
        if user_id not in self._active_connections:
            self._active_connections[user_id] = []
        self._active_connections[user_id].append(websocket)

        # Store connection info in Redis for cluster awareness
        await redis_client.hset(
            "tracking:connections",
            str(user_id),
            json.dumps({"role": role, "connected_at": datetime.now(timezone.utc).isoformat()}),
        )
        logger.info("Tracking WS connected: user=%s role=%s", user_id, role)

    async def disconnect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """Remove a WebSocket connection."""
        if user_id in self._active_connections:
            try:
                self._active_connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self._active_connections[user_id]:
                del self._active_connections[user_id]

        await redis_client.hdel("tracking:connections", str(user_id))
        logger.info("Tracking WS disconnected: user=%s", user_id)

    async def handle_location_update(
        self,
        driver_user_id: uuid.UUID,
        message: dict[str, Any],
        db: AsyncSession,
    ) -> None:
        """Process a location update from a driver and broadcast to subscribers.

        Also persists the GPS tick to Redis for the archiver worker.
        """
        lat = message.get("latitude")
        lng = message.get("longitude")
        order_id = message.get("order_id")
        speed = message.get("speed_kmh")
        heading = message.get("heading")
        accuracy = message.get("accuracy_m")
        altitude = message.get("altitude_m")
        battery = message.get("battery_pct")

        if lat is None or lng is None:
            return

        timestamp = datetime.now(timezone.utc)

        # Store latest location in Redis (fast lookup)
        location_data = {
            "driver_id": str(driver_user_id),
            "latitude": lat,
            "longitude": lng,
            "speed_kmh": speed,
            "heading": heading,
            "accuracy_m": accuracy,
            "altitude_m": altitude,
            "battery_pct": battery,
            "timestamp": timestamp.isoformat(),
            "order_id": str(order_id) if order_id else None,
        }

        # Cache latest position
        await redis_client.hset(
            "tracking:latest",
            str(driver_user_id),
            json.dumps(location_data, default=str),
        )

        # Publish for other server instances and for subscribers
        channel = f"tracking:{driver_user_id}"
        await publish(channel, location_data)

        # Publish to order-specific channel if applicable
        if order_id:
            await publish(f"tracking:order:{order_id}", location_data)

        # Queue GPS tick for archival (picked up by gps_archiver worker)
        await redis_client.lpush(
            "gps:archive_queue",
            json.dumps(location_data, default=str),
        )

        # Broadcast to connected WebSocket subscribers
        await self._broadcast_to_order_subscribers(order_id, location_data)

        logger.debug(
            "Location update: driver=%s lat=%.6f lng=%.6f",
            driver_user_id, lat, lng,
        )

    async def subscribe_to_order(
        self,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> None:
        """Subscribe a user to receive updates for a specific order."""
        if order_id not in self._order_subscribers:
            self._order_subscribers[order_id] = set()
        self._order_subscribers[order_id].add(user_id)

    async def unsubscribe_from_order(
        self,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> None:
        """Unsubscribe a user from order updates."""
        if order_id in self._order_subscribers:
            self._order_subscribers[order_id].discard(user_id)

    async def _broadcast_to_order_subscribers(
        self,
        order_id: str | None,
        data: dict[str, Any],
    ) -> None:
        """Send location data to all WebSocket clients subscribed to an order."""
        if not order_id:
            return

        try:
            oid = uuid.UUID(order_id)
        except (ValueError, TypeError):
            return

        subscribers = self._order_subscribers.get(oid, set())
        for user_id in subscribers:
            connections = self._active_connections.get(user_id, [])
            dead: list[WebSocket] = []
            for ws in connections:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                try:
                    connections.remove(ws)
                except ValueError:
                    pass
