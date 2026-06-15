"""
FastAPI application entry point for LEOPARD backend.

Sets up the ASGI app with lifespan management, CORS middleware,
and v1 API router.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import engine
from app.core.firebase import get_firebase_app
from app.core.redis import redis_client as _redis_client
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialise connections on startup, clean up on shutdown."""
    # Startup: ensure Firebase is initialised
    get_firebase_app()
    # Redis client is already created at import time — verify connectivity
    await _redis_client.ping()
    # Database engine is ready; pool will be used on first request
    yield
    # Shutdown
    await _redis_client.aclose()  # type: ignore[attr-defined]
    await engine.dispose()


app = FastAPI(
    title="LEOPARD - Freight Transport Platform",
    description="Vietnamese freight logistics platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
