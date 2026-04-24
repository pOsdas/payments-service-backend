import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.routers.payments import router as payments_router
from app.core.db_helper import db_helper


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

RETRY_ATTEMPTS = 10
RETRY_DELAY = 2.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ready = False

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        if await db_helper.ping():
            db_ready = True
            logger.info("Database is ready.")
            break

        logger.warning(
            "Database ping failed. Attempt %s/%s",
            attempt,
            RETRY_ATTEMPTS,
        )
        await asyncio.sleep(RETRY_DELAY)

    if not db_ready:
        raise RuntimeError("Database is not available after retries")

    yield

    await db_helper.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Test Backend",
        version="1.0.0",
    )
    app.include_router(payments_router, prefix="/api/v1")

    return app


app = create_app()