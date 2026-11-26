from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints

Username = Annotated[
    str, StringConstraints(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
]
Password = Annotated[SecretStr, Field(min_length=8, max_length=128)]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    password: Password


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    password: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
        ]
        | None
    )


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    old_password: Annotated[SecretStr, Field(min_length=1, max_length=128)]
    new_password: Password


class UserInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str | None


class PublicUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    additional_info: UserInfoResponse
    created_at: datetime
    updated_at: datetime


class UserResponse(PublicUserResponse):
    id: UUID


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
