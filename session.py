"""Engine y sesiones asíncronas (asyncpg)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependencia FastAPI: una sesión por request, rollback ante error."""
    get_engine()
    assert _sessionmaker is not None  # noqa: S101
    async with _sessionmaker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
