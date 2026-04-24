import asyncio
import logging

from app.broker.rabbit import broker
from app.core.config import get_settings
from app.core.db_helper import db_helper
from app.services.outbox import get_pending_outbox_events, publish_outbox_event


logger = logging.getLogger(__name__)


async def run_outbox_publisher() -> None:
    settings = get_settings()

    await broker.connect()

    logger.info("Outbox publisher started")

    try:
        while True:
            async with db_helper.session_factory() as session:
                events = await get_pending_outbox_events(
                    session=session,
                    limit=settings.outbox_batch_size,
                )

                for event in events:
                    await publish_outbox_event(
                        session=session,
                        event=event,
                    )

            await asyncio.sleep(settings.outbox_poll_interval_seconds)
    finally:
        await broker.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_outbox_publisher())