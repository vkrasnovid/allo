"""Database engine and session management."""

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://allo:allo_dev_pass@postgres:5432/allo",
)

_engine = None
_async_session_factory = None


def get_engine():
    """Lazy-create the database engine."""
    global _engine
    if _engine is None:
        try:
            _engine = create_async_engine(
                DATABASE_URL, echo=False, pool_size=5, max_overflow=10,
            )
        except Exception as e:
            logger.error(f"Failed to create engine: {e}")
            raise
    return _engine


def get_session_factory():
    """Lazy-create the session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db():
    """Dependency for getting async DB session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine():
    """Dispose the engine if it was created."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
