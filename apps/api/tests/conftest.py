import asyncio
import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://exposureflow:exposureflow@localhost:5432/exposureflow",
)
os.environ.setdefault("APP_ENV", "local")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from exposureflow_api.config import settings
from exposureflow_api.database import async_session_factory
from exposureflow_api.models import Base

TEST_DATABASE_URL = settings.database_url


async def _postgres_ready() -> bool:
    engine = create_async_engine(TEST_DATABASE_URL)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        await engine.dispose()


POSTGRES_READY = asyncio.run(_postgres_ready())


@pytest_asyncio.fixture(scope="session")
async def engine():
    if not POSTGRES_READY:
        pytest.skip("PostgreSQL is required for API integration tests.")

    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory.configure(bind=engine)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(engine) -> AsyncClient:
    from exposureflow_api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
