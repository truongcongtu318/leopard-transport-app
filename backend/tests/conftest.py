"""Shared test fixtures for LEOPARD backend."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(loop_scope="session")
async def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session per test function."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with app overrides."""
    from app.main import app
    from app.core.database import get_async_session

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client for services that use it."""
    mock = mocker.MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.publish.return_value = 1
    return mock


@pytest.fixture
def sample_user_payload() -> dict[str, Any]:
    return {
        "phone": "+84901234567",
        "full_name": "Nguyễn Văn A",
        "role": "shipper",
    }


@pytest.fixture
def sample_order_payload() -> dict[str, Any]:
    return {
        "stops": [
            {
                "sequence": 0,
                "address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
                "latitude": 10.7769,
                "longitude": 106.7009,
                "stop_type": "pickup",
                "contact_name": "Người gửi",
                "contact_phone": "+84901234567",
            },
            {
                "sequence": 1,
                "address": "456 Lê Lợi, Quận 1, TP.HCM",
                "latitude": 10.7689,
                "longitude": 106.7012,
                "stop_type": "dropoff",
                "contact_name": "Người nhận",
                "contact_phone": "+84908765432",
            },
        ],
        "items": [
            {
                "description": "Thùng hàng xi măng",
                "category": "construction",
                "weight_kg": 2500.0,
                "quantity": 1,
                "is_fragile": False,
            },
        ],
        "vehicle_type": "truck_2t_5t",
        "notes": "Giao giờ hành chính",
    }


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Mock JWT auth headers."""
    return {"Authorization": "Bearer test.mock.jwt.token"}
