from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_session


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
