"""Seed data script for development database."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_USERS = [
    {
        "firebase_uid": "admin_firebase_uid",
        "role": "admin",
        "phone": "+849****0000",
        "full_name": "Admin LEOPARD",
        "is_verified": True,
        "auth_provider": "phone",
    },
    {
        "firebase_uid": "driver_firebase_1",
        "role": "driver",
        "phone": "+849****1111",
        "full_name": "Nguyễn Văn Tài",
        "is_verified": True,
        "auth_provider": "phone",
    },
    {
        "firebase_uid": "driver_firebase_2",
        "role": "driver",
        "phone": "+849****2222",
        "full_name": "Trần Minh Quang",
        "is_verified": True,
        "auth_provider": "phone",
    },
    {
        "firebase_uid": "shipper_firebase_1",
        "role": "shipper",
        "phone": "+849****3333",
        "full_name": "Công ty VLXD Nam Phát",
        "is_verified": True,
        "auth_provider": "phone",
    },
    {
        "firebase_uid": "fleet_firebase_1",
        "role": "fleet_owner",
        "phone": "+849****4444",
        "full_name": "Đội xe Phương Nam",
        "is_verified": True,
        "auth_provider": "phone",
    },
]


async def seed_database() -> None:
    """Populate database with initial development data."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Seed users
        for user_data in SEED_USERS:
            user = User(**user_data)
            session.add(user)
        await session.flush()

        logger.info("Seeded %d users", len(SEED_USERS))

        # Seed driver profiles
        driver_user = await session.get(User, 2)  # driver_firebase_1
        if driver_user:
            driver = Driver(
                user_id=driver_user.id,
                license_number="79A-12345",
                license_expiry=datetime(2028, 12, 31, tzinfo=timezone.utc),
                is_available=True,
                approval_status="approved",
            )
            session.add(driver)
            await session.flush()

            vehicle = Vehicle(
                driver_id=driver.id,
                vehicle_type="truck_2t_5t",
                plate_number="51D-123.45",
                brand="Hyundai",
                model="HD72",
                year=2022,
                max_weight_kg=5000,
                status="active",
            )
            session.add(vehicle)
            logger.info("Seeded driver profile + vehicle")

        await session.commit()
        logger.info("Database seeding complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
