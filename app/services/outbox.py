from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker.rabbit import PAYMENTS_NEW_QUEUE, broker
from app.core.models import OutboxEvent, OutboxEventStatus


async def lock_pending_outbox_events(
    session: AsyncSession,
    limit: int,
) -> list[OutboxEvent]:
    result = await session.scalars(
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxEventStatus.pending)
        .order_by(OutboxEvent.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )

    events = list(result.all())

    for event in events:
        event.status = OutboxEventStatus.processing
        event.attempts += 1
        event.last_error = None

    await session.commit()

    return events


async def mark_outbox_event_as_published(
    session: AsyncSession,
    event_id,
) -> None:
    event = await session.get(OutboxEvent, event_id)

    if event is None:
        return

    event.status = OutboxEventStatus.published
    event.published_at = datetime.now(timezone.utc)
    event.last_error = None

    await session.commit()


async def mark_outbox_event_as_failed_or_pending(
    session: AsyncSession,
    event_id,
    error: Exception,
) -> None:
    event = await session.get(OutboxEvent, event_id)

    if event is None:
        return

    event.last_error = str(error)

    if event.attempts >= 3:
        event.status = OutboxEventStatus.failed
    else:
        event.status = OutboxEventStatus.pending

    await session.commit()


async def publish_outbox_event(
    session: AsyncSession,
    event: OutboxEvent,
) -> None:
    event_id = event.id

    try:
        await broker.publish(
            message=event.payload,
            queue=PAYMENTS_NEW_QUEUE,
        )
    except Exception as error:
        await mark_outbox_event_as_failed_or_pending(
            session=session,
            event_id=event_id,
            error=error,
        )
        return

    await mark_outbox_event_as_published(
        session=session,
        event_id=event_id,
    )