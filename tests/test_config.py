from src.config import Settings


def test_database_url_preserves_special_characters():
    settings = Settings(
        _env_file=None,
        postgres_host="db",
        postgres_db="home_manager",
        postgres_user="user@home",
        postgres_password="p@ss:/%word",
    )
    url = settings.database_url
    assert url.username == "user@home"
    assert url.password == "p@ss:/%word"
    assert url.host == "db"
    assert url.drivername == "postgresql+psycopg"
    assert "p@ss:/%word" not in repr(settings)


def test_environment_overrides_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "POSTGRES_HOST=from-file\nPOSTGRES_DB=test\n"
        "POSTGRES_USER=test\nPOSTGRES_PASSWORD=test\nHTTP_PORT=8080\n"
    )
    monkeypatch.setenv("POSTGRES_HOST", "from-environment")
    assert Settings(_env_file=env_file).postgres_host == "from-environment"
