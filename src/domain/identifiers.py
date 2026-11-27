def normalize_identifier(value: str) -> str:
    """Канонический логин пользователя или идентификатор дома."""
    return value.strip().lower()
