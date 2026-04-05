from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_helper.session_getter():
        yield session