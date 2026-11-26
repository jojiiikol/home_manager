from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.dto.users import UserProfile
from src.exceptions.users import InvalidCredentials
from src.repositories.users import UsersRepository
from src.services.users import UsersService

bearer = HTTPBearer(auto_error=False)


def get_users_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UsersService:
    return UsersService(UsersRepository(session))


UsersServiceDependency = Annotated[UsersService, Depends(get_users_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: UsersServiceDependency,
) -> UserProfile:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise error
    try:
        return await service.get_current_user(credentials.credentials)
    except InvalidCredentials:
        raise error from None


CurrentUser = Annotated[UserProfile, Depends(get_current_user)]
