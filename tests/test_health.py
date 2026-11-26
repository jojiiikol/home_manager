import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

# Проверки не требуют .env или запущенного PostgreSQL.
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")

from src.main import app  # noqa: E402


def test_health_and_openapi():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert client.get("/openapi.json").status_code == 200


def test_readiness_when_database_is_available():
    connection = AsyncMock()
    with patch("src.repositories.health.engine") as engine:
        connect = engine.connect
        connect.return_value.__aenter__ = AsyncMock(return_value=connection)
        connect.return_value.__aexit__ = AsyncMock(return_value=False)
        with TestClient(app) as client:
            assert client.get("/health/ready").status_code == 200
        connection.execute.assert_awaited_once()


def test_readiness_does_not_expose_database_errors():
    with patch("src.repositories.health.engine") as engine:
        connect = engine.connect
        connect.return_value.__aenter__ = AsyncMock(
            side_effect=OperationalError("secret connection string", {}, Exception())
        )
        with TestClient(app) as client:
            response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
