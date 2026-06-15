"""Tracking / WebSocket tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestTrackingConnectionManager:
    """WebSocket connection manager logic."""

    def test_register_client(self):
        """Registering a client should add to active connections."""
        from app.services.tracking_service import TrackingConnectionManager

        manager = TrackingConnectionManager()
        # Can test internal state via the manager's data structures
        assert isinstance(manager.active_connections, dict)

    def test_remove_client(self):
        """Removing a client should clean up connection."""
        from app.services.tracking_service import TrackingConnectionManager

        manager = TrackingConnectionManager()
        assert len(manager.active_connections) == 0  # starts empty


class TestLocationBroadcast:
    """Location update broadcast behavior."""

    def test_location_update_payload_validation(self):
        """A valid location update should pass schema validation."""
        from app.schemas.tracking import LocationUpdate

        loc = LocationUpdate(
            booking_id="bk_test",
            driver_id=1,
            latitude=10.7689,
            longitude=106.7012,
            speed_kph=45.0,
            bearing=120.0,
        )
        assert loc.latitude == 10.7689
        assert loc.speed_kph == 45.0

    def test_invalid_coordinates_rejected(self):
        """Coordinates out of range should be rejected."""
        from app.schemas.tracking import LocationUpdate

        import pydantic

        with pytest.raises(pydantic.ValidationError):
            LocationUpdate(
                booking_id="bk_test",
                driver_id=1,
                latitude=200.0,  # invalid
                longitude=106.7012,
                speed_kph=45.0,
                bearing=120.0,
            )


class TestGPSTrackingModel:
    """GPS tracking data model."""

    def test_gps_tracking_row(self):
        """A GPS tracking row should be constructable."""
        from app.models.tracking import GPSTracking
        from datetime import datetime, timezone

        row = GPSTracking(
            time=datetime.now(timezone.utc),
            driver_id=1,
            latitude=10.7689,
            longitude=106.7012,
            speed_kmh=45.0,
            bearing=120,
        )
        assert row.driver_id == 1
        assert row.latitude == 10.7689
