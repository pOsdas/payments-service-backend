from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.payment import PaymentCreateRequest
from app.core.models.outbox_event import OutboxEvent
from app.core.models.payment import Payment, PaymentStatus


PAYMENT_CREATED_EVENT_TYPE = "payment.created"


async def create_payment(
    session: AsyncSession,
    data: PaymentCreateRequest,
    idempotency_key: str,
) -> Payment:
    existing_payment = await session.scalar(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )

    if existing_payment is not None:
        return existing_payment

    payment = Payment(
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        metadata_json=data.metadata,
        status=PaymentStatus.pending,
        idempotency_key=idempotency_key,
        webhook_url=str(data.webhook_url),
    )

    session.add(payment)
    await session.flush()

    outbox_event = OutboxEvent(
        event_type=PAYMENT_CREATED_EVENT_TYPE,
        aggregate_id=payment.id,
        payload={
            "payment_id": str(payment.id),
            "amount": str(payment.amount),
            "currency": payment.currency.value,
            "description": payment.description,
            "metadata": payment.metadata_json,
            "webhook_url": payment.webhook_url,
        },
    )

    session.add(outbox_event)
    await session.commit()
    await session.refresh(payment)

    return payment


async def get_payment_by_id(
    session: AsyncSession,
    payment_id: UUID,
) -> Payment | None:
    return await session.scalar(
        select(Payment).where(Payment.id == payment_id)
    )