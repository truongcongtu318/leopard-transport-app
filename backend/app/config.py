"""
LEOPARD Backend - Application Settings

Pydantic-settings v2 based configuration.
All environment variables use the LEOPARD_ prefix.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the LEOPARD backend."""

    model_config = SettingsConfigDict(
        env_prefix="LEOPARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -- Application -------------------------------------------------------
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # -- Database -----------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://leopard:leopard@localhost:5432/leopard_db",
        description="Async PostgreSQL connection string",
    )

    @field_validator("database_url", mode="after")
    @classmethod
    def _ensure_asyncpg(cls, v: str) -> str:
        if "asyncpg" not in v:
            raise ValueError("DATABASE_URL must use asyncpg driver")
        return v

    # -- Redis --------------------------------------------------------------
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # -- JWT ----------------------------------------------------------------
    jwt_secret_key: str = Field(
        default="change-me-in-production-please",
        description="Secret key for JWT encoding",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expire_minutes: int = Field(
        default=60 * 24 * 7,
        ge=1,
        description="JWT TTL in minutes (default 7 days)",
    )

    # -- Firebase -----------------------------------------------------------
    firebase_credentials_path: str = Field(
        default="./firebase-credentials.json",
        description="Path to Firebase service account JSON",
    )

    # -- External APIs ------------------------------------------------------
    vietmap_api_key: str = Field(default="", description="Vietmap API key")
    openweather_api_key: str = Field(default="", description="OpenWeather API key")

    # -- Celery -------------------------------------------------------------
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )

    # -- Uploads ------------------------------------------------------------
    upload_dir: str = Field(default="./uploads", description="Upload directory")
    max_upload_size_mb: int = Field(
        default=10, ge=1, description="Max upload file size in MB"
    )

    # -- CORS ---------------------------------------------------------------
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return v
        return []

    # -- Derived helpers ----------------------------------------------------
    @property
    def upload_path(self) -> Path:
        """Absolute path to the upload directory."""
        p = Path(self.upload_dir)
        if not p.is_absolute():
            p = Path.cwd() / p
        return p


# Singleton - import this everywhere
settings = Settings()
