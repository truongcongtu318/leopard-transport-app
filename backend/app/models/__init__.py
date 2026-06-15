"""
Import all models so Alembic auto-generates migrations correctly.
"""

from app.models.base import Base, TimestampMixin
from app.models.user import User
from app.models.driver import Driver, DriverDocument
from app.models.vehicle import Vehicle
from app.models.business import Business, BusinessContract, BusinessDriver
from app.models.order import Order, OrderStop, OrderItem, OrderBid
from app.models.payment import Payment
from app.models.trip import ActiveTrip
from app.models.tracking import GPSTracking
from app.models.eta import ETAPrediction
from app.models.vrp import RouteOptimization
from app.models.notification import Notification, OrderStatusLog

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Driver",
    "DriverDocument",
    "Vehicle",
    "Business",
    "BusinessContract",
    "BusinessDriver",
    "Order",
    "OrderStop",
    "OrderItem",
    "OrderBid",
    "Payment",
    "ActiveTrip",
    "GPSTracking",
    "ETAPrediction",
    "RouteOptimization",
    "Notification",
    "OrderStatusLog",
]
