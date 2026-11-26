from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserAdditionalInfo:
    name: str | None


@dataclass(frozen=True, slots=True)
class UserProfile:
    id: UUID
    username: str
    additional_info: UserAdditionalInfo
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class UserCredentials:
    id: UUID
    password_hash: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str = field(repr=False)
    expires_in: int = 900
