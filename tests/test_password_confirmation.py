import pytest

from src.schemas.houses import CreateHouseRequest
from src.schemas.passwords import ChangePasswordRequest
from src.schemas.users import RegisterRequest


@pytest.mark.parametrize(
    "model, payload, field",
    [
        (
            RegisterRequest,
            {"username": "alice", "password": "original-password"},
            "password_confirmation",
        ),
        (
            CreateHouseRequest,
            {"login": "family", "name": "Дом", "password": "house-password"},
            "password_confirmation",
        ),
        (
            ChangePasswordRequest,
            {"old_password": "original-password", "new_password": "new-password"},
            "new_password_confirmation",
        ),
        (
            ChangePasswordRequest,
            {"old_password": "house-password", "new_password": "new-password"},
            "new_password_confirmation",
        ),
    ],
)
def test_password_confirmation_is_required_and_checked(model, payload, field):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        model.model_validate(payload)
    with pytest.raises(ValidationError, match="Пароли не совпадают"):
        model.model_validate({**payload, field: "different-password"})


def test_registration_mismatch_does_not_create_account(client):
    response = client.post(
        "/users",
        json={
            "username": "alice",
            "password": "original-password",
            "password_confirmation": "different-password",
        },
    )
    assert response.status_code == 422
    assert "Пароли не совпадают" in response.text
    valid = client.post(
        "/users",
        json={
            "username": "alice",
            "password": "original-password",
            "password_confirmation": "original-password",
        },
    )
    assert valid.status_code == 201
