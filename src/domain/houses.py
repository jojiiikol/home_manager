from enum import StrEnum


class ParticipantRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class ParticipantStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    LEFT = "left"
