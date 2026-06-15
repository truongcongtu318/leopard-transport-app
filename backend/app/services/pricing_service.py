"""
Pricing service — fare calculation with distance, weight, vehicle type multipliers.

Vietnamese freight rate engine with VAT and fuel surcharges.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Base rates per kilometre by vehicle type (VND/km)
VEHICLE_RATES: dict[str, float] = {
    "three_wheeler": 5_000,
    "truck_under_2t": 8_000,
    "truck_2t_5t": 12_000,
    "truck_5t_10t": 18_000,
    "truck_over_10t": 25_000,
    "container": 35_000,
}

# Weight surcharge rates (VND per kg above base)
WEIGHT_TIERS: list[tuple[float, float]] = [
    (0, 500, 0),        # first 500 kg included in base
    (500, 2000, 200),   # 200 VND/kg for 500–2000 kg
    (2000, 5000, 150),  # 150 VND/kg for 2000–5000 kg
    (5000, float("inf"), 100),  # 100 VND/kg beyond 5000 kg
]

# Cargo type multipliers
CARGO_MULTIPLIERS: dict[str, float] = {
    "general": 1.0,
    "fragile": 1.2,
    "perishable": 1.3,
    "dangerous": 1.5,
    "oversized": 1.4,
}

# Vietnam VAT rate
VAT_PCT = 8.0
FUEL_SURCHARGE_PCT = 5.0
MINIMUM_FARE_VND = 50_000


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance between two coordinates in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_duration_min(distance_km: float) -> int:
    """Estimate travel duration in minutes. Average 40 km/h for freight."""
    return max(5, int(distance_km / 40 * 60))


def _calc_weight_surcharge(weight_kg: float) -> float:
    """Calculate stepped weight surcharge in VND."""
    surcharge = 0.0
    remaining = weight_kg
    tiers = [(0, 500, 0), (500, 2000, 200), (2000, 5000, 150), (5000, float("inf"), 100)]
    for low, high, rate in tiers:
        tier_range = min(remaining, high) - low
        if tier_range > 0:
            surcharge += tier_range * rate
        remaining -= tier_range
        if remaining <= 0:
            break
    return surcharge


class PricingService:
    """Fare calculation engine for Vietnamese freight transport."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    async def calculate_fare(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        cargo_type: str = "general",
        total_weight_kg: float = 100.0,
        total_volume_cbm: float | None = None,
        vehicle_type: str | None = None,
        stops_count: int = 2,
    ) -> dict[str, Any]:
        """Calculate estimated fare with detailed breakdown."""
        # Distance
        distance_km = _haversine_km(origin_lat, origin_lng, destination_lat, destination_lng)
        # Apply road factor (roads are ~1.3x straight-line distance)
        distance_km *= 1.3
        distance_km = round(distance_km, 1)

        duration_min = _estimate_duration_min(distance_km)

        # Pick vehicle type if not specified
        if not vehicle_type:
            if total_weight_kg <= 500:
                vehicle_type = "three_wheeler"
            elif total_weight_kg <= 2000:
                vehicle_type = "truck_under_2t"
            elif total_weight_kg <= 5000:
                vehicle_type = "truck_2t_5t"
            elif total_weight_kg <= 10000:
                vehicle_type = "truck_5t_10t"
            else:
                vehicle_type = "truck_over_10t"

        rate_per_km = VEHICLE_RATES.get(vehicle_type, 10_000)
        cargo_mult = CARGO_MULTIPLIERS.get(cargo_type, 1.0)

        # Base rate
        base_rate = distance_km * rate_per_km * cargo_mult

        # Weight surcharge
        weight_surcharge = _calc_weight_surcharge(total_weight_kg)

        # Volume surcharge (if volume is large relative to weight)
        volume_surcharge = 0.0
        if total_volume_cbm and total_volume_cbm > (total_weight_kg / 250):
            volume_surcharge = total_volume_cbm * 50_000  # 50k VND per excess CBM

        # Fuel surcharge
        fuel_surcharge = base_rate * (FUEL_SURCHARGE_PCT / 100)

        # Extra stop surcharges
        extra_stops = max(0, stops_count - 2)
        stop_surcharge = extra_stops * 30_000  # 30k VND per extra stop

        # Toll estimate (simple heuristic for Vietnamese tolls)
        toll_fee = 0.0
        if distance_km > 50:
            toll_fee = math.floor(distance_km / 50) * 20_000

        subtotal = base_rate + weight_surcharge + volume_surcharge + fuel_surcharge + stop_surcharge + toll_fee
        subtotal = max(subtotal, MINIMUM_FARE_VND)

        vat_amount = subtotal * (VAT_PCT / 100)
        total = subtotal + vat_amount

        # Round to nearest 1000 VND
        total = math.ceil(total / 1000) * 1000

        return {
            "distance_km": distance_km,
            "duration_min": duration_min,
            "base_rate": base_rate,
            "weight_surcharge": weight_surcharge,
            "volume_surcharge": volume_surcharge,
            "fuel_surcharge": fuel_surcharge,
            "toll_fee_estimate": toll_fee,
            "subtotal": subtotal,
            "vat_pct": VAT_PCT,
            "vat_amount": vat_amount,
            "total": total,
            "currency": "VND",
            "breakdown": {
                "vehicle_type": vehicle_type,
                "rate_per_km": rate_per_km,
                "cargo_multiplier": cargo_mult,
                "extra_stops": extra_stops,
                "stop_surcharge": stop_surcharge,
            },
        }
