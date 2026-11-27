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
from src.schemas.identifiers import Identifier
from src.schemas.passwords import (
    PasswordConfirmationRequest,
)

HouseLogin = Identifier
HouseName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class CreateHouseRequest(PasswordConfirmationRequest):
    login: HouseLogin
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
    username: str
    name: str | None
    role: ParticipantRole
    status: ParticipantStatus
    created_at: datetime
    updated_at: datetime


class HouseListResponse(HouseResponse):
    participation: ParticipantResponse
