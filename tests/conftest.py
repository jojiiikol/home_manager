import os

# Тесты не зависят от локального .env и не используют секреты разработчика.
os.environ["JWT_SECRET_KEY"] = "test-signing-key-only-for-automated-tests-12345"
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
