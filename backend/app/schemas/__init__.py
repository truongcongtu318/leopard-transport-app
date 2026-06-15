"""Pydantic schemas for the LEOPARD API."""

# Re-export key schemas for convenience
from app.schemas.auth import (
    GoogleAuthRequest,
    OTPRequest,
    OTPVerify,
    TokenResponse,
)
from app.schemas.user import UserRead, UserUpdate
from app.schemas.driver import DriverRead, DriverUpdate
from app.schemas.vehicle import VehicleCreate, VehicleRead
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderRead,
    OrderStopCreate,
)
from app.schemas.bid import BidCreate, BidRead
from app.schemas.payment import (
    FareCalcRequest,
    FareCalcResponse,
    VietQRRequest,
    VietQRResponse,
)
from app.schemas.tracking import LocationUpdate, TrackingEvent
from app.schemas.eta import ETAPredictRequest, ETAPredictResponse
from app.schemas.vrp import VRPOptimizeRequest, VRPOptimizeResponse
from app.schemas.notification import NotificationRead
from app.schemas.dashboard import FleetStats

__all__ = [
    "GoogleAuthRequest",
    "OTPRequest",
    "OTPVerify",
    "TokenResponse",
    "UserRead",
    "UserUpdate",
    "DriverRead",
    "DriverUpdate",
    "VehicleCreate",
    "VehicleRead",
    "OrderCreate",
    "OrderItemCreate",
    "OrderRead",
    "OrderStopCreate",
    "BidCreate",
    "BidRead",
    "FareCalcRequest",
    "FareCalcResponse",
    "VietQRRequest",
    "VietQRResponse",
    "LocationUpdate",
    "TrackingEvent",
    "ETAPredictRequest",
    "ETAPredictResponse",
    "VRPOptimizeRequest",
    "VRPOptimizeResponse",
    "NotificationRead",
    "FleetStats",
]
