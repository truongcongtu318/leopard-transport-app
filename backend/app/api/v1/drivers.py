"""
Driver routes — profile, document upload, status updates.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.schemas.driver import DriverDocumentRead, DriverRead, DriverUpdate
from app.services.document_service import DocumentService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=DriverRead, summary="Get driver profile")
async def get_driver_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DriverRead:
    """Return the authenticated user's driver profile."""
    service = UserService(db)
    driver = await service.get_driver_profile(current_user)
    return driver


@router.put("/me", response_model=DriverRead, summary="Update driver profile")
async def update_driver_profile(
    body: DriverUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DriverRead:
    """Update the driver's profile (license info, etc.)."""
    service = UserService(db)
    driver = await service.update_driver_profile(current_user, body)
    return driver


@router.post(
    "/me/documents",
    response_model=DriverDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a driver document",
)
async def upload_driver_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
) -> DriverDocumentRead:
    """Upload a document (license, ID card, vehicle registration, insurance)."""
    doc_service = DocumentService(db)
    user_service = UserService(db)
    driver = await user_service.get_driver_profile(current_user)
    document = await doc_service.upload_document(
        driver_id=driver.id,
        document_type=document_type,
        file=file,
    )
    return document


@router.get(
    "/me/documents",
    response_model=list[DriverDocumentRead],
    summary="List driver documents",
)
async def list_driver_documents(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[DriverDocumentRead]:
    """List all documents uploaded by the driver."""
    doc_service = DocumentService(db)
    user_service = UserService(db)
    driver = await user_service.get_driver_profile(current_user)
    documents = await doc_service.get_driver_documents(driver.id)
    return documents


@router.patch("/me/online", summary="Toggle driver online status")
async def toggle_online_status(
    is_online: bool = Form(...),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Set the driver's online/offline status."""
    service = UserService(db)
    await service.set_driver_online(current_user, is_online)
    return {"status": "online" if is_online else "offline"}
