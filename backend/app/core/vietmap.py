"""
Vietmap API client for geocoding, routing, and distance matrix operations.

Vietmap is a Vietnamese map/geolocation API provider.
"""

from __future__ import annotations

import httpx

from app.config import settings

VIETMAP_BASE_URL = "https://maps.vietmap.vn/api"


class VietmapClient:
    """Async HTTP client for Vietmap APIs."""

    def __init__(self) -> None:
        self.api_key = settings.vietmap_api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=VIETMAP_BASE_URL,
                timeout=httpx.Timeout(15.0),
                params={"apikey": self.api_key},
            )
        return self._client

    async def geocode(self, address: str) -> dict:
        """Convert an address string to coordinates (lat, lng)."""
        client = await self._get_client()
        resp = await client.get("/autocomplete/v3", params={"text": address, "size": 1})
        resp.raise_for_status()
        return resp.json()

    async def reverse_geocode(self, lat: float, lng: float) -> dict:
        """Convert coordinates to an address."""
        client = await self._get_client()
        resp = await client.get("/reverse/v3", params={"lat": lat, "lng": lng})
        resp.raise_for_status()
        return resp.json()

    async def get_route(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ) -> dict:
        """Calculate a driving route between two points.

        Returns distance (meters) and duration (seconds).
        """
        client = await self._get_client()
        resp = await client.get(
            "/route",
            params={
                "point": f"{origin[0]},{origin[1]}",
                "point": f"{destination[0]},{destination[1]}",
                "vehicle": "truck",
                "type": "json",
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def distance_matrix(
        self,
        origins: list[tuple[float, float]],
        destinations: list[tuple[float, float]],
    ) -> dict:
        """Compute a distance/duration matrix between multiple points."""
        client = await self._get_client()
        resp = await client.post(
            "/distance-matrix",
            json={
                "origins": [f"{lat},{lng}" for lat, lng in origins],
                "destinations": [f"{lat},{lng}" for lat, lng in destinations],
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


vietmap_client = VietmapClient()
