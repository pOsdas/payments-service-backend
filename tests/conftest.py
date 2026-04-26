import pytest

from app.core.db_helper import db_helper


@pytest.fixture(scope="session", autouse=True)
async def dispose_engine_after_tests() -> None:
    yield
    await db_helper.dispose()