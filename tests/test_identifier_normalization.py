import anyio
import pytest
from sqlalchemy import select

from src.models.houses import House
from src.models.users import User
from src.schemas.houses import JoinHouseRequest, UpdateHouseRequest
from src.schemas.users import LoginRequest


def test_normalized_logins_and_house_identifiers(client):
    password = "  CaseSensitivePassword  "
    body = {
        "username": "  ALIce  ",
        "password": password,
        "password_confirmation": password,
    }
    response = client.post("/users", json=body)
    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert client.post("/users", json={**body, "username": "AlIcE"}).status_code == 409
    response = client.post(
        "/auth/token", json={"username": "  ALICE\t", "password": password}
    )
    assert response.status_code == 200
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    # Пароль не должен менять ни регистр, ни пробелы.
    assert (
        client.post(
            "/auth/token", json={"username": "alice", "password": password.strip()}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/token", json={"username": "alice", "password": password.lower()}
        ).status_code
        == 401
    )
    house_body = {
        "login": "  FaMiLy.Home  ",
        "name": "Наш Дом",
        "password": password,
        "password_confirmation": password,
    }
    response = client.post("/houses", headers=headers, json=house_body)
    assert response.status_code == 201
    house_id = response.json()["id"]
    assert response.json()["login"] == "family.home"
    assert (
        client.post(
            "/houses", headers=headers, json={**house_body, "login": "FAMILY.HOME"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/houses/join",
            headers=headers,
            json={"login": " FAMILY.HOME ", "password": password},
        ).status_code
        == 409
    )
    response = client.patch(
        f"/houses/{house_id}", headers=headers, json={"login": "  NEW.Home  "}
    )
    assert response.status_code == 200
    assert response.json()["login"] == "new.home"
    assert (
        client.post(
            "/houses/join",
            headers=headers,
            json={"login": " NEW.HOME ", "password": password},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/houses", headers=headers, json={**house_body, "login": "NeW.HoMe"}
        ).status_code
        == 409
    )

    async def inspect():
        async with client.test_sessions() as session:
            assert (await session.scalars(select(User.username))).all() == ["alice"]
            assert (await session.scalars(select(House.login))).all() == ["new.home"]

    anyio.run(inspect)


@pytest.mark.parametrize(
    "model, field",
    [
        (LoginRequest, "username"),
        (JoinHouseRequest, "login"),
        (UpdateHouseRequest, "login"),
    ],
)
@pytest.mark.parametrize("value", ["   ", "  ab  ", "hello world", "abc\tdef", 123])
def test_identifier_validation_after_normalization(model, field, value):
    from pydantic import ValidationError

    body = {field: value}
    if model is not UpdateHouseRequest:
        body["password"] = "password"
    with pytest.raises(ValidationError):
        model.model_validate(body)
