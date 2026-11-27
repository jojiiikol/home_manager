from uuid import uuid4

import anyio
import pytest
from sqlalchemy import func, select

from src.models.houses import House, HouseInfo, HouseParticipant
from src.security.passwords import verify_password


@pytest.fixture
def actors(client):
    result = []
    for username in ["alice", "bob", "outsider"]:
        response = client.post(
            "/users",
            json={
                "username": username,
                "password": "user-password",
                "password_confirmation": "user-password",
            },
        )
        assert response.status_code == 201
        token = client.post(
            "/auth/token", json={"username": username, "password": "user-password"}
        ).json()["access_token"]
        result.append((response.json()["id"], {"Authorization": f"Bearer {token}"}))
    return result


def create(client, headers, login="family"):
    response = client.post(
        "/houses",
        headers=headers,
        json={
            "login": login,
            "password": "house-password",
            "name": "Дом семьи",
            "password_confirmation": "house-password",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def join(client, headers, login="family", password="house-password"):
    return client.post(
        "/houses/join", headers=headers, json={"login": login, "password": password}
    )


def test_create_house_and_unique_login_are_atomic(client, actors):
    user_id, headers = actors[0]
    house = create(client, headers)
    assert house["additional_info"] == {"name": "Дом семьи"}
    assert "password_hash" not in house and "password" not in house
    membership = client.get(
        f"/houses/{house['id']}/participants/me", headers=headers
    ).json()
    assert membership["user_id"] == user_id
    assert membership["role"] == "admin" and membership["status"] == "active"
    assert (
        client.post(
            "/houses",
            headers=headers,
            json={
                "login": "family",
                "password": "another-password",
                "name": "Дубликат",
                "password_confirmation": "another-password",
            },
        ).status_code
        == 409
    )

    async def inspect():
        async with client.test_sessions() as session:
            for model in [House, HouseInfo, HouseParticipant]:
                assert (
                    await session.scalar(select(func.count()).select_from(model)) == 1
                )
            stored = await session.scalar(select(House))
            assert stored.password_hash != "house-password"
            assert verify_password("house-password", stored.password_hash)

    anyio.run(inspect)


def test_join_leave_rejoin_keeps_membership_and_resets_role(client, actors):
    alice, bob, _ = actors
    house = create(client, alice[1])
    base = f"/houses/{house['id']}"
    assert join(client, bob[1], password="wrong").status_code == 400
    assert join(client, bob[1], login="missing").status_code == 400
    response = join(client, bob[1])
    assert response.status_code == 200
    original = response.json()
    assert original["role"] == "member" and original["status"] == "active"
    assert join(client, bob[1]).status_code == 409
    assert len(client.get(base + "/participants", headers=bob[1]).json()) == 2
    assert (
        client.patch(
            base + f"/participants/{bob[0]}", headers=alice[1], json={"role": "admin"}
        ).status_code
        == 200
    )
    left = client.post(base + "/leave", headers=bob[1]).json()
    assert left["status"] == "left" and left["id"] == original["id"]
    assert client.get(base, headers=bob[1]).status_code == 200
    assert client.get(base + "/participants/me", headers=bob[1]).status_code == 200
    assert client.get(base + "/participants", headers=bob[1]).status_code == 403
    returned = join(client, bob[1]).json()
    assert returned["id"] == original["id"]
    assert returned["created_at"] == original["created_at"]
    assert returned["role"] == "member" and returned["status"] == "active"
    houses = client.get("/houses", headers=bob[1]).json()
    assert [item["id"] for item in houses] == [house["id"]]
    assert houses[0]["participation"]["role"] == "member"
    assert houses[0]["participation"]["status"] == "active"


def test_block_restore_and_access_boundaries(client, actors):
    alice, bob, outsider = actors
    house = create(client, alice[1])
    other = create(client, outsider[1], "another")
    base = f"/houses/{house['id']}"
    join(client, bob[1])
    for headers in [bob[1], outsider[1]]:
        assert (
            client.patch(base, headers=headers, json={"name": "Подмена"}).status_code
            == 403
        )
        assert (
            client.patch(
                base + f"/participants/{alice[0]}",
                headers=headers,
                json={"role": "member"},
            ).status_code
            == 403
        )
        assert (
            client.put(
                base + "/password",
                headers=headers,
                json={
                    "old_password": "house-password",
                    "new_password": "new-password",
                    "new_password_confirmation": "new-password",
                },
            ).status_code
            == 403
        )
    assert client.get(base, headers=outsider[1]).status_code == 403
    assert client.get(base + "/participants/me", headers=outsider[1]).status_code == 403
    assert client.get(base + "/participants", headers=outsider[1]).status_code == 403
    assert (
        client.patch(
            base + f"/participants/{outsider[0]}",
            headers=alice[1],
            json={"status": "blocked"},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/houses/{other['id']}/participants/{bob[0]}",
            headers=alice[1],
            json={"status": "blocked"},
        ).status_code
        == 403
    )
    client.patch(
        base + f"/participants/{bob[0]}", headers=alice[1], json={"role": "admin"}
    )
    blocked = client.patch(
        base + f"/participants/{bob[0]}", headers=alice[1], json={"status": "blocked"}
    ).json()
    assert blocked["status"] == "blocked"
    assert join(client, bob[1]).status_code == 403
    assert client.post(base + "/leave", headers=bob[1]).status_code == 403
    assert client.get(base, headers=bob[1]).status_code == 200
    assert (
        client.get(base + "/participants/me", headers=bob[1]).json()["status"]
        == "blocked"
    )
    assert client.get(base + "/participants", headers=bob[1]).status_code == 403
    assert (
        client.patch(base, headers=bob[1], json={"name": "Подмена"}).status_code == 403
    )
    assert (
        client.patch(
            base + f"/participants/{bob[0]}",
            headers=alice[1],
            json={"status": "active", "role": "admin"},
        ).status_code
        == 409
    )
    restored = client.patch(
        base + f"/participants/{bob[0]}", headers=alice[1], json={"status": "active"}
    ).json()
    assert restored["id"] == blocked["id"]
    assert restored["role"] == "member" and restored["status"] == "active"


@pytest.mark.parametrize(
    "change",
    [
        {"role": "member"},
        {"status": "left"},
        {"status": "blocked"},
        {"role": "member", "status": "blocked"},
    ],
)
def test_last_admin_cannot_be_removed(client, actors, change):
    alice, bob, _ = actors
    house = create(client, alice[1])
    base = f"/houses/{house['id']}"
    assert client.post(base + "/leave", headers=alice[1]).status_code == 409
    assert (
        client.patch(
            base + f"/participants/{alice[0]}", headers=alice[1], json=change
        ).status_code
        == 409
    )
    join(client, bob[1])
    assert (
        client.patch(
            base + f"/participants/{bob[0]}", headers=alice[1], json={"role": "admin"}
        ).status_code
        == 200
    )
    assert (
        client.patch(
            base + f"/participants/{alice[0]}", headers=bob[1], json=change
        ).status_code
        == 200
    )
    assert client.post(base + "/leave", headers=bob[1]).status_code == 409


def test_login_name_password_and_existing_memberships(client, actors):
    alice, bob, outsider = actors
    house = create(client, alice[1])
    create(client, alice[1], "occupied")
    base = f"/houses/{house['id']}"
    join(client, bob[1])
    assert (
        client.patch(
            base, headers=alice[1], json={"login": "occupied", "name": "Не сохранять"}
        ).status_code
        == 409
    )
    assert (
        client.get(base, headers=alice[1]).json()["additional_info"]["name"]
        == "Дом семьи"
    )
    response = client.patch(
        base, headers=alice[1], json={"login": "new-login", "name": "Новое имя"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["additional_info"] == {"name": "Новое имя"}
    assert join(client, outsider[1]).status_code == 400
    body = {
        "old_password": "wrong",
        "new_password": "new-password",
        "new_password_confirmation": "new-password",
    }
    assert (
        client.put(base + "/password", headers=alice[1], json=body).status_code == 400
    )
    body["old_password"] = "house-password"
    assert (
        client.put(base + "/password", headers=alice[1], json=body).status_code == 204
    )
    assert client.get(base, headers=bob[1]).status_code == 200
    assert join(client, outsider[1], login="new-login").status_code == 400
    assert (
        join(
            client, outsider[1], login="new-login", password="new-password"
        ).status_code
        == 200
    )
    assert len(client.get("/houses", headers=alice[1]).json()) == 2


def test_house_endpoints_require_token(client):
    base = f"/houses/{uuid4()}"
    for method, path, body in [
        (
            "POST",
            "/houses",
            {
                "login": "family",
                "name": "Дом",
                "password": "house-password",
                "password_confirmation": "house-password",
            },
        ),
        ("GET", "/houses", None),
        ("GET", base, None),
        ("POST", "/houses/join", {"login": "family", "password": "house-password"}),
        ("GET", base + "/participants", None),
        ("GET", base + "/participants/me", None),
        ("POST", base + "/leave", None),
        ("PATCH", base, {"name": "Новое имя"}),
        (
            "PUT",
            base + "/password",
            {
                "old_password": "old-password",
                "new_password": "new-password",
                "new_password_confirmation": "new-password",
            },
        ),
        ("PATCH", base + f"/participants/{uuid4()}", {"role": "admin"}),
    ]:
        assert client.request(method, path, json=body).status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": None},
        {"name": " "},
        {"login": None},
        {"login": "a"},
        {"password_hash": "fake"},
    ],
)
def test_house_update_validation(client, actors, body):
    house = create(client, actors[0][1])
    assert (
        client.patch(
            f"/houses/{house['id']}", headers=actors[0][1], json=body
        ).status_code
        == 422
    )


def test_admin_can_restore_left_member_without_house_password(client, actors):
    alice, bob, _ = actors
    house = create(client, alice[1])
    base = f"/houses/{house['id']}"
    original = join(client, bob[1]).json()
    assert client.post(base + "/leave", headers=bob[1]).status_code == 200
    response = client.patch(
        base + f"/participants/{bob[0]}",
        headers=alice[1],
        json={"status": "active"},
    )
    assert response.status_code == 200
    restored = response.json()
    assert restored["id"] == original["id"]
    assert restored["created_at"] == original["created_at"]
    assert restored["role"] == "member" and restored["status"] == "active"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"role": None},
        {"status": None},
        {"role": "owner"},
        {"status": "inactive"},
        {"user_id": str(uuid4())},
    ],
)
def test_participant_update_validation(client, actors, body):
    alice, bob, _ = actors
    house = create(client, alice[1])
    join(client, bob[1])
    response = client.patch(
        f"/houses/{house['id']}/participants/{bob[0]}",
        headers=alice[1],
        json=body,
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"login": "family", "password": "house-password"},
        {
            "login": "family",
            "password": "house-password",
            "name": None,
            "password_confirmation": "house-password",
        },
        {
            "login": "family",
            "password": "house-password",
            "name": " ",
            "password_confirmation": "house-password",
        },
        {
            "login": "family",
            "password": "short",
            "name": "Дом",
            "password_confirmation": "short",
        },
    ],
)
def test_house_creation_validation(client, actors, body):
    assert client.post("/houses", headers=actors[0][1], json=body).status_code == 422


def test_participant_names_and_membership_status_for_interface(client, actors):
    alice, bob, _ = actors
    house = create(client, alice[1])
    base = f"/houses/{house['id']}"
    join(client, bob[1])
    client.patch("/users/me", headers=bob[1], json={"name": "Борис"})
    roster = client.get(base + "/participants", headers=alice[1]).json()
    assert next(item for item in roster if item["user_id"] == bob[0])["name"] == "Борис"
    creator = next(item for item in roster if item["user_id"] == alice[0])
    assert creator["name"] is None and creator["username"] == "alice"
    assert client.post(base + "/leave", headers=bob[1]).status_code == 200
    listing = client.get("/houses", headers=bob[1]).json()
    assert listing[0]["participation"]["status"] == "left"
    assert listing[0]["participation"]["name"] == "Борис"


def test_mismatched_confirmation_does_not_change_house_or_passwords(client, actors):
    alice, bob, _ = actors
    create_body = {
        "login": "family",
        "name": "Дом",
        "password": "house-password",
        "password_confirmation": "another-password",
    }
    assert client.post("/houses", headers=alice[1], json=create_body).status_code == 422
    assert client.get("/houses", headers=alice[1]).json() == []
    house = create(client, alice[1])
    change = {
        "old_password": "house-password",
        "new_password": "new-password",
        "new_password_confirmation": "another-password",
    }
    assert (
        client.put(
            f"/houses/{house['id']}/password", headers=alice[1], json=change
        ).status_code
        == 422
    )
    assert join(client, bob[1]).status_code == 200
    change["old_password"] = "user-password"
    assert (
        client.put("/users/me/password", headers=alice[1], json=change).status_code
        == 422
    )
    assert (
        client.post(
            "/auth/token", json={"username": "alice", "password": "user-password"}
        ).status_code
        == 200
    )
