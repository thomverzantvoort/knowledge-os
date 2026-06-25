from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_async_engine() -> AsyncEngine:
    global _async_engine, _async_session_factory
    if _async_engine is None:
        _async_engine = create_async_engine(
            settings.async_database_url,
            pool_pre_ping=True,
        )
        _async_session_factory = async_sessionmaker(
            bind=_async_engine,
            expire_on_commit=False,
        )
    return _async_engine


@contextmanager
def get_session() -> Iterator[Session]:
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    session = _session_factory()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    if _async_session_factory is None:
        get_async_engine()
    assert _async_session_factory is not None
    session = _async_session_factory()
    try:
        yield session
    finally:
        await session.close()
