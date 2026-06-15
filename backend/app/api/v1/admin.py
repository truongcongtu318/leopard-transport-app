"""
Admin routes — user management, document approval.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, get_db
from app.models.driver import DriverDocument
from app.models.user import User
from app.schemas.driver import DriverDocumentRead
from app.schemas.user import UserRead
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/users",
    response_model=list[UserRead],
    summary="List all users (admin)",
)
async def list_users(
    admin_user: AdminUser,
    db: AsyncSession = Depends(get_db),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[User]:
    """List all users with optional role and active filter. Admin only."""
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Get user by ID (admin)",
)
async def get_user(
    user_id: uuid.UUID,
    admin_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get a specific user by ID. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/users/{user_id}/activate",
    summary="Activate / deactivate a user (admin)",
)
async def toggle_user_active(
    user_id: uuid.UUID,
    is_active: bool = Query(...),
    admin_user: AdminUser = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Activate or deactivate a user account. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    db.add(user)
    return {"status": "active" if is_active else "deactivated", "user_id": str(user_id)}


@router.get(
    "/documents/pending",
    response_model=list[DriverDocumentRead],
    summary="List pending driver documents (admin)",
)
async def list_pending_documents(
    admin_user: AdminUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[DriverDocument]:
    """List all driver documents with pending status. Admin only."""
    stmt = (
        select(DriverDocument)
        .where(DriverDocument.status == "pending")
        .order_by(DriverDocument.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.patch(
    "/documents/{document_id}/approve",
    response_model=DriverDocumentRead,
    summary="Approve a driver document (admin)",
)
async def approve_document(
    document_id: uuid.UUID,
    admin_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> DriverDocument:
    """Approve a driver document. Admin only."""
    doc_service = DocumentService(db)
    document = await doc_service.approve_document(document_id, admin_user.id)
    return document


@router.patch(
    "/documents/{document_id}/reject",
    response_model=DriverDocumentRead,
    summary="Reject a driver document (admin)",
)
async def reject_document(
    document_id: uuid.UUID,
    review_note: str = Query(...),
    admin_user: AdminUser = None,
    db: AsyncSession = Depends(get_db),
) -> DriverDocument:
    """Reject a driver document with a review note. Admin only."""
    doc_service = DocumentService(db)
    document = await doc_service.reject_document(
        document_id, admin_user.id, review_note
    )
    return document
