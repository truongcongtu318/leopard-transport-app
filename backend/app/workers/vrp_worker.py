"""
VRP worker — Celery task for asynchronous route optimisation.

Heavy optimisation runs are offloaded to Celery so the API can return
a task ID immediately and the client polls for results.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="leopard.vrp.optimize",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def optimise_routes_task(
    self,
    vehicles: list[dict[str, Any]],
    stops: list[dict[str, Any]],
    depot_lat: float,
    depot_lng: float,
    solver_time_limit_s: int = 30,
    priority: str = "distance",
    requested_by: str | None = None,
) -> dict[str, Any]:
    """Celery task that runs the VRP solver asynchronously.

    Args:
        vehicles: Serialised vehicle definitions.
        stops: Serialised stop definitions.
        depot_lat / depot_lng: Depot coordinates.
        solver_time_limit_s: Max solver time.
        priority: Optimization target.
        requested_by: User UUID string.

    Returns:
        dict: Solver result payload.
    """
    from app.services.vrp_service import VRPBatchOptimizationService

    logger.info(
        "VRP task started: %d vehicles, %d stops, limit=%ds",
        len(vehicles), len(stops), solver_time_limit_s,
    )

    service = VRPBatchOptimizationService(db=None)

    # Run the async solver in a sync context (Celery worker)
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            service.optimize(
                vehicles=vehicles,
                stops=stops,
                depot_lat=depot_lat,
                depot_lng=depot_lng,
                solver_time_limit_s=solver_time_limit_s,
                priority=priority,
                requested_by=uuid.UUID(requested_by) if requested_by else None,
            )
        )
    except Exception as exc:
        logger.exception("VRP task failed")
        self.retry(exc=exc)
        return {"solver_status": "error", "error": str(exc)}
    finally:
        loop.close()

    logger.info(
        "VRP task completed: status=%s, time=%dms",
        result.get("solver_status"), result.get("solver_time_ms", 0),
    )
    return result
