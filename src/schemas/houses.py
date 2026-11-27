from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    StringConstraints,
    model_validator,
)

from src.domain.houses import ParticipantRole, ParticipantStatus

HouseLogin = Annotated[
    str, StringConstraints(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
]
HouseName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
HousePassword = Annotated[SecretStr, Field(min_length=8, max_length=128)]


class CreateHouseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: HouseLogin
    password: HousePassword
    name: HouseName


class JoinHouseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: HouseLogin
    password: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class UpdateHouseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: HouseLogin | None = None
    name: HouseName | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set or any(
            getattr(self, field) is None for field in self.model_fields_set
        ):
            raise ValueError("Provide at least one non-null login or name")
        return self


class ChangeHousePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    old_password: Annotated[SecretStr, Field(min_length=1, max_length=128)]
    new_password: HousePassword


class UpdateParticipantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: ParticipantRole | None = None
    status: ParticipantStatus | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set or any(
            getattr(self, field) is None for field in self.model_fields_set
        ):
            raise ValueError("Provide at least one non-null role or status")
        return self


class HouseInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class HouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    login: str
    additional_info: HouseInfoResponse
    created_at: datetime
    updated_at: datetime


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    house_id: UUID
    user_id: UUID
    role: ParticipantRole
    status: ParticipantStatus
    created_at: datetime
    updated_at: datetime
