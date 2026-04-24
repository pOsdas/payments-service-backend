import asyncio
import logging
import signal

from app.broker.rabbit import broker
from app.core.config import get_settings
from app.core.db_helper import db_helper
from app.services.outbox import lock_pending_outbox_events, publish_outbox_event


logger = logging.getLogger(__name__)


async def run_outbox_publisher() -> None:
    settings = get_settings()
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await broker.connect()
    logger.info("Outbox publisher started")

    try:
        while not stop_event.is_set():
            async with db_helper.session_factory() as session:
                events = await lock_pending_outbox_events(
                    session=session,
                    limit=settings.outbox_batch_size,
                )

                for event in events:
                    if stop_event.is_set():
                        break

                    await publish_outbox_event(
                        session=session,
                        event=event,
                    )

            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=settings.outbox_poll_interval_seconds,
                )
            except asyncio.TimeoutError:
                pass

    finally:
        await broker.close()
        logger.info("Outbox publisher stopped gracefully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_outbox_publisher())