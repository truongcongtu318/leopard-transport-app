"""
GPS archiver — Celery periodic task that drains Redis GPS queue to TimescaleDB.

Runs every 30 seconds to batch-insert GPS ticks from Redis into the
gps_tracking hypertable for long-term storage.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

ARCHIVE_CHUNK_SIZE = 100


@celery_app.task(
    name="leopard.gps.archive",
    bind=True,
    acks_late=True,
)
def archive_gps_batch_task(self) -> dict:
    """Drain the GPS archive queue from Redis and persist to TimescaleDB.

    Called periodically by Celery Beat (every 30 seconds).
    """
    import redis.asyncio as aioredis
    from app.config import settings

    async def _archive():
        redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        records: list[dict] = []

        # Pop a batch of GPS records from Redis queue
        for _ in range(ARCHIVE_CHUNK_SIZE):
            data = await redis.rpop("gps:archive_queue")
            if data is None:
                break
            try:
                records.append(json.loads(data))
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in GPS archive queue")
                continue

        await redis.aclose()

        if not records:
            return {"archived": 0}

        # Bulk insert into database
        from app.core.database import async_session_factory
        from app.repositories.tracking_repo import TrackingRepository

        async with async_session_factory() as session:
            repo = TrackingRepository()
            count = await repo.bulk_insert(session, records)
            await session.commit()
            return {"archived": count}

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_archive())
    except Exception as exc:
        logger.exception("GPS archiver task failed")
        return {"archived": 0, "error": str(exc)}
    finally:
        loop.close()

    logger.info("GPS archiver: archived %d records", result.get("archived", 0))
    return result
