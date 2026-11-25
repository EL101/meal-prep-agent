import os
import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Tests run against in-memory SQLite; set before app modules build the engine.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app import models  # noqa: E402,F401
from app.api.deps import current_user_id, get_queue  # noqa: E402
from app.db import Base, get_session  # noqa: E402
from app.main import create_app  # noqa: E402

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
async def sessionmaker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def queue() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
async def client(sessionmaker, queue) -> AsyncIterator[AsyncClient]:
    app = create_app(use_lifespan=False)

    async def _session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as s:
            yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[current_user_id] = lambda: USER_ID
    app.dependency_overrides[get_queue] = lambda: queue
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
