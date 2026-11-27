from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints

from src.schemas.identifiers import Identifier
from src.schemas.passwords import PasswordConfirmationRequest

Username = Identifier


class RegisterRequest(PasswordConfirmationRequest):
    username: Username


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
