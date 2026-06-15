"""
Document service — driver document upload, approval, rejection.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.driver import DriverDocument

logger = logging.getLogger(__name__)

ALLOWED_DOCUMENT_TYPES = [
    "license_front",
    "license_back",
    "id_card_front",
    "id_card_back",
    "vehicle_registration",
    "insurance",
]

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class DocumentService:
    """Handles driver document uploads and admin approval workflows."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload_document(
        self,
        driver_id: uuid.UUID,
        document_type: str,
        file: UploadFile,
    ) -> DriverDocument:
        """Upload a document file for a driver.

        Saves to disk under ``settings.upload_path`` and creates DB record.
        """
        if document_type not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}",
            )

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")

        content_type = file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{content_type}' not allowed. "
                f"Accepted: {', '.join(ALLOWED_MIME_TYPES)}",
            )

        # Check if a document of this type already exists and is pending/approved
        existing = await self.db.execute(
            select(DriverDocument).where(
                DriverDocument.driver_id == driver_id,
                DriverDocument.document_type == document_type,
                DriverDocument.status.in_(["pending", "approved"]),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A {document_type} document already exists. "
                "Please replace or reject the existing one first.",
            )

        # Save file
        upload_dir = settings.upload_path
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_ext = os.path.splitext(file.filename)[1] or ".bin"
        stored_filename = f"{driver_id}_{document_type}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = upload_dir / stored_filename

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB",
            )

        file_path.write_bytes(content)

        # Create DB record
        document = DriverDocument(
            driver_id=driver_id,
            document_type=document_type,
            file_url=f"/uploads/{stored_filename}",
            status="pending",
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        logger.info(
            "Document uploaded: driver=%s type=%s file=%s",
            driver_id, document_type, stored_filename,
        )
        return document

    async def get_driver_documents(
        self,
        driver_id: uuid.UUID,
    ) -> list[DriverDocument]:
        """List all documents for a driver."""
        result = await self.db.execute(
            select(DriverDocument)
            .where(DriverDocument.driver_id == driver_id)
            .order_by(DriverDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def approve_document(
        self,
        document_id: uuid.UUID,
        reviewer_id: uuid.UUID,
    ) -> DriverDocument:
        """Approve a pending document. Admin only."""
        result = await self.db.execute(
            select(DriverDocument).where(DriverDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        if document.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is already {document.status}",
            )

        document.status = "approved"
        document.reviewed_by = reviewer_id
        document.reviewed_at = datetime.now(timezone.utc)
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        logger.info(
            "Document %s approved by %s", document_id, reviewer_id,
        )
        return document

    async def reject_document(
        self,
        document_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        review_note: str,
    ) -> DriverDocument:
        """Reject a pending document with a review note. Admin only."""
        result = await self.db.execute(
            select(DriverDocument).where(DriverDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        if document.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is already {document.status}",
            )

        document.status = "rejected"
        document.review_note = review_note
        document.reviewed_by = reviewer_id
        document.reviewed_at = datetime.now(timezone.utc)
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        logger.info(
            "Document %s rejected by %s: %s", document_id, reviewer_id, review_note,
        )
        return document
