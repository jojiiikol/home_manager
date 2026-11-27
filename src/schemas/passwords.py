from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationInfo,
    field_validator,
)

Password = Annotated[SecretStr, Field(min_length=8, max_length=128)]


class PasswordConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: Password
    password_confirmation: Password

    @field_validator("password_confirmation")
    @classmethod
    def passwords_match(cls, value: SecretStr, info: ValidationInfo) -> SecretStr:
        password = info.data.get("password")
        if password and password.get_secret_value() != value.get_secret_value():
            raise ValueError("Пароли не совпадают")
        return value


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    old_password: Annotated[SecretStr, Field(min_length=1, max_length=128)]
    new_password: Password
    new_password_confirmation: Password

    @field_validator("new_password_confirmation")
    @classmethod
    def passwords_match(cls, value: SecretStr, info: ValidationInfo) -> SecretStr:
        password = info.data.get("new_password")
        if password and password.get_secret_value() != value.get_secret_value():
            raise ValueError("Пароли не совпадают")
        return value
