"""
Aggregator router that includes all v1 route modules.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.drivers import router as drivers_router
from app.api.v1.vehicles import router as vehicles_router
from app.api.v1.orders import router as orders_router
from app.api.v1.bidding import router as bidding_router
from app.api.v1.payments import router as payments_router
from app.api.v1.tracking import router as tracking_router
from app.api.v1.eta import router as eta_router
from app.api.v1.vrp import router as vrp_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.admin import router as admin_router
from app.api.v1.dashboard import router as dashboard_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(drivers_router, prefix="/drivers", tags=["Drivers"])
api_v1_router.include_router(vehicles_router, prefix="/vehicles", tags=["Vehicles"])
api_v1_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_v1_router.include_router(bidding_router, prefix="/bidding", tags=["Bidding"])
api_v1_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_v1_router.include_router(tracking_router, prefix="/tracking", tags=["Tracking"])
api_v1_router.include_router(eta_router, prefix="/eta", tags=["ETA"])
api_v1_router.include_router(vrp_router, prefix="/bookings", tags=["VRP"])
api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
