"""Async SQLAlchemy engine and session setup."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from src.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _build_engine():
    settings = get_settings()
    engine_kwargs: dict = {"future": True}
    if ":memory:" in settings.database_url:
        # In-memory SQLite needs a single shared connection (StaticPool) so every
        # session sees the same database -- used by the test suite.
        engine_kwargs["poolclass"] = StaticPool
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_async_engine(settings.database_url, **engine_kwargs)


engine = _build_engine()
_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session
