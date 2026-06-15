"""
ETA worker — Celery task for async ETA prediction and persistence.

Runs the XGBoost model off the request path and stores results
in the eta_predictions table.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="leopard.eta.predict",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    acks_late=True,
)
def predict_eta_task(
    self,
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    vehicle_type: str | None = None,
    cargo_weight_kg: float | None = None,
    departure_time: str | None = None,
    order_id: str | None = None,
) -> dict:
    """Celery task for async ETA prediction with DB persistence.

    Args:
        origin_lat / origin_lng: Start point coordinates.
        destination_lat / destination_lng: End point coordinates.
        vehicle_type: Vehicle classification.
        cargo_weight_kg: Weight of cargo.
        departure_time: ISO-8601 departure timestamp string.
        order_id: Associated order UUID string.

    Returns:
        dict: ETA prediction result.
    """
    from app.services.eta_service import ETAService

    logger.info(
        "ETA task: (%.4f, %.4f) -> (%.4f, %.4f)",
        origin_lat, origin_lng, destination_lat, destination_lng,
    )

    if departure_time:
        from dateutil.parser import isoparse
        dt = isoparse(departure_time)
    else:
        dt = datetime.utcnow()

    service = ETAService(db=None)

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            service.predict(
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                destination_lat=destination_lat,
                destination_lng=destination_lng,
                vehicle_type=vehicle_type,
                cargo_weight_kg=cargo_weight_kg,
                departure_time=dt,
                order_id=uuid.UUID(order_id) if order_id else None,
            )
        )
    except Exception as exc:
        logger.exception("ETA prediction task failed")
        self.retry(exc=exc)
        return {"error": str(exc)}
    finally:
        loop.close()

    # Persist prediction to database
    try:
        _persist_eta_prediction(order_id, origin_lat, origin_lng, destination_lat, destination_lng, result)
    except Exception as exc:
        logger.warning("Failed to persist ETA prediction: %s", exc)

    logger.info(
        "ETA prediction: %.1f km -> %d min (conf=%.2f)",
        result["distance_km"], result["predicted_duration_min"], result["confidence_score"],
    )
    return result


def _persist_eta_prediction(
    order_id: str | None,
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    result: dict,
) -> None:
    """Persist the ETA prediction to the database (sync path in Celery worker)."""
    import asyncio
    from app.core.database import async_session_factory
    from app.models.eta import ETAPrediction

    async def _save():
        async with async_session_factory() as session:
            prediction = ETAPrediction(
                order_id=uuid.UUID(order_id) if order_id else uuid.uuid4(),
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                destination_lat=destination_lat,
                destination_lng=destination_lng,
                distance_km=result["distance_km"],
                predicted_duration_min=result["predicted_duration_min"],
                confidence_score=result["confidence_score"],
                model_version=result.get("model_version", "haversine-fallback"),
                weather_data={},
                traffic_data={"traffic_multiplier": result.get("factors", {}).get("traffic_multiplier", 1.0)},
                features_vector=result.get("factors", {}),
            )
            session.add(prediction)
            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_save())
    except Exception:
        pass
    finally:
        loop.close()
