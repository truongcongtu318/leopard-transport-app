"""
Payment service — VietQR generation, payment status tracking.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import VietQRResponse

logger = logging.getLogger(__name__)

# Default bank config for LEOPARD platform
DEFAULT_BANK_CODE = "970422"  # MB Bank BIN
DEFAULT_ACCOUNT_NUMBER = "0123456789"
DEFAULT_ACCOUNT_NAME = "LEOPARD LOGISTICS JSC"


class PaymentService:
    """VietQR code generation and payment management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_vietqr(
        self,
        order_id: uuid.UUID,
        amount: float,
        payer_id: uuid.UUID,
        bank_code: str | None = None,
        account_number: str | None = None,
        description: str | None = None,
    ) -> VietQRResponse:
        """Generate a VietQR payment code and persist payment record."""
        # Verify the order exists
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        bank_code = bank_code or DEFAULT_BANK_CODE
        account_number = account_number or DEFAULT_ACCOUNT_NUMBER

        # Generate transaction ID
        txn_hash = hashlib.sha256(
            f"{order_id}:{payer_id}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        transaction_id = f"LP{txn_hash.upper()}"

        # VietQR description (max 25 chars)
        if not description:
            description = f"LP {order.tracking_code}"
        description = description[:25]

        # Build VietQR EMVCo payload
        qr_payload = self._build_vietqr_emvco(
            bank_code=bank_code,
            account_number=account_number,
            amount=amount,
            description=description,
        )
        qr_code_base64 = base64.b64encode(qr_payload.encode()).decode()

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        # Determine payee (driver or platform)
        payee_id = payer_id  # Placeholder — in reality, route to driver's user_id

        # Create payment record
        payment = Payment(
            order_id=order_id,
            payer_id=payer_id,
            payee_id=payee_id,
            amount=amount,
            currency="VND",
            payment_method="vietqr",
            status="pending",
            transaction_id=transaction_id,
            vietqr_data=qr_payload,
            payment_metadata={
                "bank_code": bank_code,
                "account_number": account_number,
                "description": description,
                "expires_at": expires_at.isoformat(),
            },
        )
        self.db.add(payment)
        await self.db.flush()

        logger.info(
            "VietQR generated for order %s, txn=%s, amount=%.0f VND",
            order.tracking_code, transaction_id, amount,
        )

        return VietQRResponse(
            qr_code_base64=qr_code_base64,
            transaction_id=transaction_id,
            payment_url=f"https://api.vietqr.io/v2/{bank_code}/{account_number}/{int(amount)}",
            bank_code=bank_code,
            account_number=account_number,
            account_name=DEFAULT_ACCOUNT_NAME,
            amount=amount,
            description=description,
            expires_at=expires_at,
        )

    def _build_vietqr_emvco(
        self,
        bank_code: str,
        account_number: str,
        amount: float,
        description: str,
    ) -> str:
        """Build EMVCo QR payload string for VietQR.

        Follows NAPAS VietQR EMVCo spec for interbank transfers.
        """
        # Simplified EMVCo TLV builder
        parts = [
            "000201",  # Payload Format Indicator
            "010212",  # Point of initiation (dynamic)
        ]
        # Merchant Account Info (ID 38 — NAPAS)
        napas_payload = f"0010A000000727{len(f'01{bank_code}'):02d}01{bank_code}{len(f'02{account_number}'):02d}02{account_number}"
        parts.append(f"38{len(napas_payload):02d}{napas_payload}")
        parts.append("5303704")  # Currency (704 = VND)
        amount_str = f"{int(amount)}"
        parts.append(f"54{len(amount_str):02d}{amount_str}")
        parts.append("5802VN")  # Country
        desc_tlv = f"08{len(description):02d}{description}"
        parts.append(f"62{len(desc_tlv):02d}{desc_tlv}")
        # CRC placeholder
        data = "".join(parts) + "6304"
        crc = self._crc16_ccitt(data)
        return data + f"{crc:04X}"

    @staticmethod
    def _crc16_ccitt(data: str) -> int:
        """CRC-16/CCITT-FALSE as used in EMVCo QR codes."""
        crc = 0xFFFF
        for byte in data.encode("ascii"):
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return crc

    async def get_payment(self, payment_id: uuid.UUID) -> Payment | None:
        """Get a payment by ID."""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def list_order_payments(self, order_id: uuid.UUID) -> list[Payment]:
        """List all payments for an order."""
        result = await self.db.execute(
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())
