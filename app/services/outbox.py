from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker.rabbit import PAYMENTS_NEW_QUEUE, broker
from app.core.models import OutboxEvent, OutboxEventStatus


async def get_pending_outbox_events(
    session: AsyncSession,
    limit: int,
) -> list[OutboxEvent]:
    result = await session.scalars(
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxEventStatus.pending)
        .order_by(OutboxEvent.created_at)
        .limit(limit)
    )

    return list(result.all())


async def mark_outbox_event_as_published(
    session: AsyncSession,
    event: OutboxEvent,
) -> None:
    event.status = OutboxEventStatus.published
    event.published_at = datetime.now(timezone.utc)
    event.last_error = None

    await session.commit()


async def mark_outbox_event_as_failed(
    session: AsyncSession,
    event: OutboxEvent,
    error: Exception,
) -> None:
    event.attempts += 1
    event.last_error = str(error)

    if event.attempts >= 3:
        event.status = OutboxEventStatus.failed

    await session.commit()


async def publish_outbox_event(
    session: AsyncSession,
    event: OutboxEvent,
) -> None:
    try:
        await broker.publish(
            message=event.payload,
            queue=PAYMENTS_NEW_QUEUE,
        )
    except Exception as error:
        await mark_outbox_event_as_failed(
            session=session,
            event=event,
            error=error,
        )
        return

    await mark_outbox_event_as_published(
        session=session,
        event=event,
    )