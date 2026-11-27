from typing import Annotated

from pydantic import BeforeValidator, StringConstraints

from src.domain.identifiers import normalize_identifier

Identifier = Annotated[
    str,
    StringConstraints(min_length=3, max_length=64, pattern=r"^[a-z0-9_.-]+$"),
    BeforeValidator(
        lambda value: normalize_identifier(value) if isinstance(value, str) else value
    ),
]
