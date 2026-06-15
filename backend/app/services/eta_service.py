"""
ETA service — XGBoost inference wrapper with haversine fallback.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Try to import XGBoost — gracefully degrade if not available
_xgb_model = None
try:
    import xgboost as xgb
    import numpy as np

    _HAS_XGB = True
except ImportError:
    _HAS_XGB = False
    logger.warning("XGBoost not available; ETA will use haversine fallback")


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Vehicle speed estimates (km/h) for different types
VEHICLE_SPEEDS: dict[str, float] = {
    "three_wheeler": 30.0,
    "truck_under_2t": 45.0,
    "truck_2t_5t": 40.0,
    "truck_5t_10t": 35.0,
    "truck_over_10t": 30.0,
    "container": 25.0,
}

# Time-of-day traffic multipliers (hour -> multiplier)
TRAFFIC_MULTIPLIERS: dict[int, float] = {
    7: 1.6, 8: 1.8, 9: 1.4,  # Morning rush
    17: 1.5, 18: 1.7, 19: 1.4,  # Evening rush
    12: 1.1,  # Lunch
}


def _load_model():
    """Load the XGBoost model from disk (lazy singleton)."""
    global _xgb_model
    if _xgb_model is None and _HAS_XGB:
        try:
            _xgb_model = xgb.Booster()
            _xgb_model.load_model("models/eta_xgboost.json")
            logger.info("XGBoost ETA model loaded successfully")
        except Exception as exc:
            logger.warning("Could not load XGBoost model: %s — using fallback", exc)
            _xgb_model = None


class ETAService:
    """ETA prediction using XGBoost with haversine fallback."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    async def predict(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        vehicle_type: str | None = None,
        cargo_weight_kg: float | None = None,
        departure_time: datetime | None = None,
        order_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Predict ETA for a route segment.

        Returns predicted duration, arrival time, distance, and confidence.
        """
        distance_km = _haversine_km(origin_lat, origin_lng, destination_lat, destination_lng)
        # Apply road distance factor
        distance_km *= 1.3
        distance_km = round(distance_km, 1)

        if departure_time is None:
            departure_time = datetime.now(timezone.utc)

        # Attempt XGBoost prediction
        predicted_min, confidence, model_version = await self._xgb_predict(
            distance_km=distance_km,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            vehicle_type=vehicle_type,
            cargo_weight_kg=cargo_weight_kg,
            departure_time=departure_time,
        )

        # Weather impact (simplified)
        weather_impact = 0.0
        # In production: call OpenWeather API
        # weather_data = await get_weather(origin_lat, origin_lng)

        # Traffic impact
        hour = departure_time.hour
        traffic_mult = TRAFFIC_MULTIPLIERS.get(hour, 1.0)
        traffic_impact = round((traffic_mult - 1.0) * 100, 1)

        predicted_arrival = departure_time + timedelta(minutes=predicted_min)

        return {
            "predicted_duration_min": predicted_min,
            "predicted_arrival": predicted_arrival,
            "distance_km": distance_km,
            "confidence_score": confidence,
            "model_version": model_version,
            "weather_impact_pct": weather_impact,
            "traffic_impact_pct": traffic_impact,
            "factors": {
                "vehicle_type": vehicle_type or "default",
                "cargo_weight_kg": cargo_weight_kg,
                "departure_hour": hour,
                "traffic_multiplier": traffic_mult,
                "distance_km": distance_km,
            },
        }

    async def _xgb_predict(
        self,
        distance_km: float,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        vehicle_type: str | None,
        cargo_weight_kg: float | None,
        departure_time: datetime,
    ) -> tuple[int, float, str]:
        """Try XGBoost model inference; fall back to haversine estimation.

        Returns:
            (predicted_minutes, confidence_score, model_version)
        """
        if _HAS_XGB:
            _load_model()

        if _xgb_model is not None and _HAS_XGB:
            try:
                # Build feature vector
                hour = departure_time.hour
                day_of_week = departure_time.weekday()
                is_rush = 1 if hour in (7, 8, 9, 17, 18, 19) else 0
                weight = cargo_weight_kg or 0.0

                # Vehicle type encoding
                vehicle_types = [
                    "three_wheeler", "truck_under_2t", "truck_2t_5t",
                    "truck_5t_10t", "truck_over_10t", "container",
                ]
                vehicle_encoded = vehicle_types.index(vehicle_type) if vehicle_type in vehicle_types else 1

                features = np.array([[
                    distance_km,
                    origin_lat, origin_lng,
                    destination_lat, destination_lng,
                    hour, day_of_week, is_rush,
                    weight, vehicle_encoded,
                ]])

                dmatrix = xgb.DMatrix(features)
                prediction = _xgb_model.predict(dmatrix)
                predicted_min = max(5, int(round(float(prediction[0]))))
                return predicted_min, 0.85, "xgboost-v1"

            except Exception as exc:
                logger.warning("XGBoost prediction failed: %s — using fallback", exc)

        # Haversine fallback
        return self._haversine_fallback(
            distance_km, vehicle_type, cargo_weight_kg, departure_time
        )

    def _haversine_fallback(
        self,
        distance_km: float,
        vehicle_type: str | None,
        cargo_weight_kg: float | None,
        departure_time: datetime,
    ) -> tuple[int, float, str]:
        """Fallback ETA estimation using haversine distance and speed tables."""
        speed = VEHICLE_SPEEDS.get(vehicle_type or "truck_2t_5t", 40.0)

        # Adjust speed for cargo weight
        if cargo_weight_kg and cargo_weight_kg > 5000:
            speed *= 0.85
        elif cargo_weight_kg and cargo_weight_kg > 2000:
            speed *= 0.92

        # Traffic adjustment
        hour = departure_time.hour
        traffic_mult = TRAFFIC_MULTIPLIERS.get(hour, 1.0)

        base_min = distance_km / speed * 60
        adjusted_min = base_min * traffic_mult

        # Add buffer for loading/unloading
        adjusted_min += 15

        predicted_min = max(5, int(round(adjusted_min)))
        confidence = 0.55  # Lower confidence for fallback

        return predicted_min, confidence, "haversine-fallback"
