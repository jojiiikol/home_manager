from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError

from src.config import get_settings
from src.dto.users import AccessToken
from src.exceptions.users import InvalidCredentials

ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(minutes=15)


def create_access_token(user_id: UUID) -> AccessToken:
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + TOKEN_LIFETIME},
        get_settings().jwt_secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )
    return AccessToken(value=token, expires_in=int(TOKEN_LIFETIME.total_seconds()))


def decode_access_token(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret_key.get_secret_value(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
        return UUID(payload["sub"])
    except InvalidTokenError, ValueError, TypeError, AttributeError:
        raise InvalidCredentials from None
