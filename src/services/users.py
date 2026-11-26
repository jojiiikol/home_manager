from uuid import UUID

from anyio import to_thread

from src.dto.users import AccessToken, UserProfile
from src.exceptions.users import IncorrectPassword, InvalidCredentials, UserNotFound
from src.repositories.users import UsersRepository
from src.security.passwords import dummy_hash, hash_password, verify_password
from src.security.tokens import create_access_token, decode_access_token


class UsersService:
    def __init__(self, repository: UsersRepository):
        self.repository = repository

    async def register(self, username: str, password: str) -> UserProfile:
        password_hash = await to_thread.run_sync(hash_password, password)
        return await self.repository.create(username, password_hash)

    async def authenticate(self, username: str, password: str) -> AccessToken:
        credentials = await self.repository.get_credentials_by_username(username)
        valid = await to_thread.run_sync(
            verify_password,
            password,
            credentials.password_hash if credentials else dummy_hash,
        )
        if not credentials or not valid:
            raise InvalidCredentials
        return create_access_token(credentials.id)

    async def get_current_user(self, token: str) -> UserProfile:
        user_id = decode_access_token(token)
        profile = await self.repository.get_profile(user_id)
        if profile is None:
            raise InvalidCredentials
        return profile

    async def get_profile(self, user_id: UUID) -> UserProfile:
        profile = await self.repository.get_profile(user_id)
        if profile is None:
            raise UserNotFound
        return profile

    async def update_profile(self, user_id: UUID, name: str | None) -> UserProfile:
        await self.repository.update_name(user_id, name)
        return await self.get_profile(user_id)

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        credentials = await self.repository.get_credentials_for_update(user_id)
        if credentials is None:
            raise UserNotFound
        if not await to_thread.run_sync(
            verify_password, old_password, credentials.password_hash
        ):
            raise IncorrectPassword
        password_hash = await to_thread.run_sync(hash_password, new_password)
        await self.repository.update_password(user_id, password_hash)
