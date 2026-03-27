from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data_source.vector_store import VectorStoreManager
from app.models.base import Base
from app.processing.memory import VectorizedMessageHistory


@pytest.fixture(scope="session")
async def engine():
    # Use SQLite in-memory for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    from app.core.db import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def db_session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        # Rollback after each test to keep it clean
        await session.rollback()


@pytest.fixture
def mock_history_db():
    db = MagicMock(spec=VectorizedMessageHistory)
    db.search_history.return_value = ""
    db.add_message = AsyncMock()
    return db


@pytest.fixture
def vector_manager():
    """VectorStoreManager com Chroma, OpenAIEmbeddings e HybridRetriever mockados."""
    with (
        patch("app.data_source.vector_store.Chroma"),
        patch("app.data_source.vector_store.OpenAIEmbeddings"),
        patch("app.data_source.vector_store.HybridRetriever"),
    ):
        vm = VectorStoreManager()
        yield vm
