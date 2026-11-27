import os

import anyio
import pytest

# Тесты не зависят от локального .env и не используют секреты разработчика.
os.environ["JWT_SECRET_KEY"] = "test-signing-key-only-for-automated-tests-12345"
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")


@pytest.fixture
def client(tmp_path):
    from fastapi.testclient import TestClient
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from src.database import Base, get_session
    from src.main import app

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'users.db'}", poolclass=NullPool
    )

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def session_override():
        async with sessions() as session:
            yield session

    anyio.run(setup)
    app.dependency_overrides[get_session] = session_override
    try:
        with TestClient(app) as test_client:
            test_client.test_sessions = sessions
            yield test_client
    finally:
        app.dependency_overrides.clear()
        anyio.run(engine.dispose)
