from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.domain.houses import ParticipantRole, ParticipantStatus


@dataclass(frozen=True, slots=True)
class HouseAdditionalInfo:
    name: str


@dataclass(frozen=True, slots=True)
class HouseProfile:
    id: UUID
    login: str
    additional_info: HouseAdditionalInfo
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class HouseCredentials:
    id: UUID
    password_hash: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class Participant:
    id: UUID
    house_id: UUID
    user_id: UUID
    username: str
    name: str | None
    role: ParticipantRole
    status: ParticipantStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class HouseListItem(HouseProfile):
    participation: Participant
