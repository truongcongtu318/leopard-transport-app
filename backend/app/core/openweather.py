"""
OpenWeather API client for weather-aware ETA adjustments.
"""

from __future__ import annotations

import httpx

from app.config import settings

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


class OpenWeatherClient:
    """Async HTTP wrapper around the OpenWeather API."""

    def __init__(self) -> None:
        self.api_key = settings.openweather_api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=OPENWEATHER_BASE_URL,
                timeout=httpx.Timeout(10.0),
            )
        return self._client

    async def get_current_weather(self, lat: float, lon: float) -> dict:
        """Fetch current weather at a given coordinate.

        Returns the full OpenWeather JSON response including ``main``,
        ``wind``, ``weather``, ``visibility`` fields.
        """
        client = await self._get_client()
        resp = await client.get(
            "/weather",
            params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_weather_conditions(self, lat: float, lon: float) -> dict:
        """Return a simplified weather conditions dict for ETA adjustment.

        Keys: ``rain``, ``wind_speed``, ``visibility``, ``temperature``.
        """
        data = await self.get_current_weather(lat, lon)
        return {
            "rain": data.get("rain", {}).get("1h", 0.0),
            "wind_speed": data.get("wind", {}).get("speed", 0.0),
            "visibility": data.get("visibility", 10000),
            "temperature": data.get("main", {}).get("temp", 25.0),
            "weather_main": data.get("weather", [{}])[0].get("main", "Clear"),
        }

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


openweather_client = OpenWeatherClient()
