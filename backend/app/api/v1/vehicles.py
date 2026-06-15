"""
Vehicle CRUD routes.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.repositories.base_repo import BaseRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=VehicleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vehicle",
)
async def create_vehicle(
    body: VehicleCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Vehicle:
    """Register a new vehicle owned by the current user."""
    repo = BaseRepository(Vehicle)
    vehicle = Vehicle(
        owner_id=current_user.id,
        license_plate=body.license_plate,
        vehicle_type=body.vehicle_type,
        brand=body.brand,
        model=body.model,
        year_of_manufacture=body.year_of_manufacture,
        max_payload_kg=body.max_payload_kg,
        max_volume_cbm=body.max_volume_cbm,
        length_m=body.length_m,
        width_m=body.width_m,
        height_m=body.height_m,
        features=body.features or [],
    )
    created = await repo.create(db, vehicle)
    return created


@router.get("/", response_model=list[VehicleRead], summary="List user's vehicles")
async def list_vehicles(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[Vehicle]:
    """List all vehicles owned by the current user."""
    repo = BaseRepository(Vehicle)
    vehicles = await repo.list_by(db, {"owner_id": current_user.id})
    return vehicles


@router.get("/{vehicle_id}", response_model=VehicleRead, summary="Get vehicle by ID")
async def get_vehicle(
    vehicle_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Vehicle:
    """Get a specific vehicle by ID."""
    repo = BaseRepository(Vehicle)
    vehicle = await repo.get(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleRead, summary="Update vehicle")
async def update_vehicle(
    vehicle_id: uuid.UUID,
    body: VehicleUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Vehicle:
    """Update a vehicle's details."""
    repo = BaseRepository(Vehicle)
    vehicle = await repo.get(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    update_data = body.model_dump(exclude_unset=True)
    updated = await repo.update(db, vehicle, update_data)
    return updated


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete vehicle",
)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a vehicle."""
    repo = BaseRepository(Vehicle)
    vehicle = await repo.get(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    await repo.delete(db, vehicle)
