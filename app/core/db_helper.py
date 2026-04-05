import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class DatabaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        pool_recycle: int = 600,
        pool_size: int = 5,
    ) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle,
            pool_size=pool_size,
        )

        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                logger.exception("Database session error")
                raise

    async def ping(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                await conn.execute(
                    text("SELECT 1"),
                    execution_options={"isolation_level": "AUTOCOMMIT"},
                )
            return True
        except Exception:
            logger.exception("Database ping failed")
            return False


settings = get_settings()
db_helper = DatabaseHelper(
    url=str(settings.db.database_url),
    echo=settings.db.db_echo,
    echo_pool=settings.db.db_echo_pool,
    pool_size=settings.db.db_pool_size,
    pool_pre_ping=settings.db.db_pool_pre_ping,
    pool_recycle=settings.db.db_pool_recycle,
    max_overflow=settings.db.db_max_overflow,
)