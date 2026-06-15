"""
Redis client, pubsub, and cache helpers.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

redis_client: aioredis.Redis = aioredis.from_url(
    settings.redis_url,
    decode_responses=True,
    max_connections=20,
)


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client."""
    return redis_client


async def cache_get(key: str) -> Any | None:
    """Retrieve a JSON-serialised value from Redis cache."""
    data = await redis_client.get(key)
    if data is not None:
        return json.loads(data)
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Store a JSON-serialised value in Redis cache with TTL (seconds)."""
    await redis_client.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(key: str) -> None:
    """Delete a cache entry by key."""
    await redis_client.delete(key)


async def publish(channel: str, message: dict[str, Any]) -> None:
    """Publish a JSON message to a Redis Pub/Sub channel."""
    await redis_client.publish(channel, json.dumps(message, default=str))


async def rate_limit_check(
    key: str,
    max_requests: int = 10,
    window_seconds: int = 60,
) -> bool:
    """Token-bucket rate limiter backed by Redis.

    Returns ``True`` if the request is allowed, ``False`` if rate-limited.
    """
    current = await redis_client.get(key)
    if current is None:
        pipe = redis_client.pipeline()
        pipe.set(key, 1, ex=window_seconds)
        await pipe.execute()
        return True

    if int(current) >= max_requests:
        return False

    await redis_client.incr(key)
    return True
