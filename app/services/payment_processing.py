import asyncio
import random
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.payment import Payment, PaymentStatus
from app.services.webhook import send_payment_webhook


def build_payment_webhook_payload(payment: Payment) -> dict[str, Any]:
    return {
        "payment_id": str(payment.id),
        "status": payment.status.value,
        "amount": str(payment.amount),
        "currency": payment.currency.value,
        "description": payment.description,
        "metadata": payment.metadata_json,
        "created_at": payment.created_at.isoformat(),
        "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
    }


async def process_payment(
    session: AsyncSession,
    message: dict[str, Any],
) -> dict[str, Any]:
    payment_id = UUID(message["payment_id"])

    payment = await session.scalar(
        select(Payment).where(Payment.id == payment_id)
    )

    if payment is None:
        raise ValueError(f"Payment {payment_id} not found")

    if payment.status != PaymentStatus.pending:
        webhook_payload = build_payment_webhook_payload(payment)

        await send_payment_webhook(
            webhook_url=payment.webhook_url,
            payload=webhook_payload,
        )

        return {
            **webhook_payload,
            "message": "Payment was already processed, webhook resent",
        }

    await asyncio.sleep(random.randint(2, 5))

    is_success = random.random() <= 0.9

    payment.status = PaymentStatus.succeeded if is_success else PaymentStatus.failed
    payment.processed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(payment)

    webhook_payload = build_payment_webhook_payload(payment)

    await send_payment_webhook(
        webhook_url=payment.webhook_url,
        payload=webhook_payload,
    )

    return webhook_payload
