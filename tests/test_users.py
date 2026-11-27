from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import anyio
import jwt
import pytest
from sqlalchemy import select, update

from src.config import get_settings
from src.models.users import User, UserInfo
from src.security.passwords import verify_password


def register(client, username="alice"):
    response = client.post(
        "/users", json={"username": username, "password": "original-password"}
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client, username="alice", password="original-password"):
    response = client.post(
        "/auth/token", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_registration_creates_profile_and_hash_atomically(client):
    user = register(client)
    assert set(user) == {
        "id",
        "username",
        "additional_info",
        "created_at",
        "updated_at",
    }
    assert user["additional_info"] == {"name": None}
    assert (
        client.post(
            "/users", json={"username": "alice", "password": "other-password"}
        ).status_code
        == 409
    )

    async def inspect_database():
        async with client.test_sessions() as session:
            users = (await session.scalars(select(User))).all()
            profiles = (await session.scalars(select(UserInfo))).all()
            assert len(users) == len(profiles) == 1
            assert users[0].id == profiles[0].user_id
            assert profiles[0].name is None
            assert users[0].password_hash != "original-password"
            assert verify_password("original-password", users[0].password_hash)
            assert users[0].created_at is not None
            assert profiles[0].updated_at is not None

    anyio.run(inspect_database)


def test_login_and_token_lifetime(client):
    user = register(client)
    token = login(client)
    payload = jwt.decode(
        token, get_settings().jwt_secret_key.get_secret_value(), algorithms=["HS256"]
    )
    assert payload["sub"] == user["id"]
    assert payload["exp"] - payload["iat"] == 900
    for username, password in [("alice", "wrong"), ("missing", "wrong")]:
        response = client.post(
            "/auth/token", json={"username": username, "password": password}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid username or password"}


def test_profiles_are_protected_and_users_only_modify_themselves(client):
    alice = register(client)
    bob = register(client, "bob")
    headers = auth(login(client))
    assert client.get(f"/users/{bob['id']}").status_code == 401
    assert client.get("/users/me").status_code == 401
    assert client.patch("/users/me", json={"name": "Alice"}).status_code == 401
    response = client.patch("/users/me", json={"name": " Alice "}, headers=headers)
    assert response.status_code == 200
    updated_alice = response.json()
    assert updated_alice["additional_info"] == {"name": "Alice"}
    assert updated_alice["id"] == alice["id"]
    assert updated_alice["created_at"] == alice["created_at"]
    assert client.get(f"/users/{bob['id']}", headers=headers).json() == {
        "username": "bob",
        "additional_info": {"name": None},
        "created_at": bob["created_at"],
        "updated_at": bob["updated_at"],
    }
    assert client.get(f"/users/{alice['id']}", headers=headers).json() == {
        "username": "alice",
        "additional_info": {"name": "Alice"},
        "created_at": updated_alice["created_at"],
        "updated_at": updated_alice["updated_at"],
    }
    assert (
        client.patch("/users/me", json={"name": None}, headers=headers).json()[
            "additional_info"
        ]["name"]
        is None
    )
    assert (
        client.patch(
            "/users/me", json={"name": "hacked", "user_id": bob["id"]}, headers=headers
        ).status_code
        == 422
    )
    assert client.get(f"/users/{uuid4()}", headers=headers).status_code == 404


def test_password_change_requires_token_and_old_password(client):
    register(client)
    headers = auth(login(client))
    body = {"old_password": "wrong", "new_password": "new-password"}
    assert client.put("/users/me/password", json=body).status_code == 401
    assert (
        client.put("/users/me/password", json=body, headers=headers).status_code == 400
    )
    login(client)
    body["old_password"] = "original-password"
    response = client.put("/users/me/password", json=body, headers=headers)
    assert response.status_code == 204
    assert response.content == b""
    assert (
        client.post(
            "/auth/token", json={"username": "alice", "password": "original-password"}
        ).status_code
        == 401
    )
    login(client, password="new-password")


@pytest.mark.parametrize(
    "kind",
    ["expired", "wrong-key", "missing-exp", "bad-sub", "deleted-user", "malformed"],
)
def test_invalid_tokens_are_rejected(client, kind):
    user = register(client)
    now = datetime.now(UTC)
    payload = {"sub": user["id"], "iat": now, "exp": now + timedelta(minutes=15)}
    key = get_settings().jwt_secret_key.get_secret_value()
    if kind == "expired":
        payload["iat"] = now - timedelta(minutes=20)
        payload["exp"] = now - timedelta(minutes=5)
    elif kind == "wrong-key":
        key = "another-secret-key-of-at-least-32-characters"
    elif kind == "missing-exp":
        del payload["exp"]
    elif kind == "bad-sub":
        payload["sub"] = "invalid-uuid"
    elif kind == "deleted-user":
        payload["sub"] = str(uuid4())
    token = jwt.encode(payload, key, algorithm="HS256")
    if kind == "malformed":
        token = "this-is-not-a-jwt"
    response = client.get("/users/me", headers=auth(token))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "body",
    [
        {"username": "ab", "password": "long-password"},
        {"username": "with space", "password": "long-password"},
        {"username": "alice", "password": "short"},
        {"username": "alice", "password": "long-password", "name": "Alice"},
    ],
)
def test_registration_validation(client, body):
    assert client.post("/users", json=body).status_code == 422


@pytest.mark.parametrize("latest_table", ["account", "profile"])
def test_profile_dates_include_changes_in_both_tables(client, latest_table):
    user = register(client)
    headers = auth(login(client))
    created_at = datetime(2025, 1, 1, tzinfo=UTC)
    older = created_at + timedelta(days=1)
    newer = created_at + timedelta(days=2)

    async def set_dates():
        async with client.test_sessions() as session:
            await session.execute(
                update(User)
                .where(User.id == UUID(user["id"]))
                .values(
                    created_at=created_at,
                    updated_at=newer if latest_table == "account" else older,
                )
            )
            await session.execute(
                update(UserInfo)
                .where(UserInfo.user_id == UUID(user["id"]))
                .values(
                    updated_at=newer if latest_table == "profile" else older,
                )
            )
            await session.commit()

    anyio.run(set_dates)
    for path in ["/users/me", f"/users/{user['id']}"]:
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        body = response.json()
        # SQLite возвращает naive datetime; PostgreSQL хранит timezone-aware.
        assert (
            datetime.fromisoformat(body["created_at"]).replace(tzinfo=UTC) == created_at
        )
        assert datetime.fromisoformat(body["updated_at"]).replace(tzinfo=UTC) == newer
        assert "password_hash" not in body
