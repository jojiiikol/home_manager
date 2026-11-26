from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    database_available: bool
