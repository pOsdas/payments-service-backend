import asyncio
import logging
from typing import Any

from faststream import FastStream

from app.broker.rabbit import PAYMENTS_DLQ_QUEUE, PAYMENTS_NEW_QUEUE, broker
from app.core.config import get_settings
from app.core.db_helper import db_helper
from app.services.payment_processing import process_payment


logger = logging.getLogger(__name__)

app = FastStream(broker)


async def publish_to_dlq(
    message: dict[str, Any],
    error: Exception,
    attempts: int,
) -> None:
    await broker.publish(
        message={
            "original_message": message,
            "error": str(error),
            "attempts": attempts,
        },
        queue=PAYMENTS_DLQ_QUEUE,
    )


@broker.subscriber(PAYMENTS_NEW_QUEUE)
async def handle_new_payment(message: dict[str, Any]) -> None:
    settings = get_settings()

    last_error: Exception | None = None

    for attempt in range(1, settings.payment_processing_max_attempts + 1):
        try:
            async with db_helper.session_factory() as session:
                result = await process_payment(
                    session=session,
                    message=message,
                )

            logger.info(
                "Payment processed successfully. payment_id=%s attempt=%s result=%s",
                message.get("payment_id"),
                attempt,
                result,
            )
            return

        except Exception as error:
            last_error = error

            logger.exception(
                "Payment processing attempt failed. payment_id=%s attempt=%s",
                message.get("payment_id"),
                attempt,
            )

            if attempt < settings.payment_processing_max_attempts:
                delay = settings.payment_processing_retry_base_delay_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

    if last_error is None:
        last_error = RuntimeError("Unknown payment processing error")

    await publish_to_dlq(
        message=message,
        error=last_error,
        attempts=settings.payment_processing_max_attempts,
    )

    logger.error(
        "Payment message sent to DLQ. payment_id=%s attempts=%s",
        message.get("payment_id"),
        settings.payment_processing_max_attempts,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(app.run())