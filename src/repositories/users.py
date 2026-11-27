from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.identifiers import normalize_identifier
from src.dto.users import UserAdditionalInfo, UserCredentials, UserProfile
from src.exceptions.users import UsernameAlreadyExists
from src.models.users import User, UserInfo


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, username: str, password_hash: str) -> UserProfile:
        user = User(
            username=normalize_identifier(username),
            password_hash=password_hash,
            info=UserInfo(),
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            # PostgreSQL сообщает имя ограничения; SQLite используется в тестах.
            constraint = getattr(
                getattr(error.orig, "diag", None), "constraint_name", None
            )
            if constraint == "uq_users_table_username" or (
                self.session.bind.dialect.name == "sqlite"
                and "UNIQUE constraint failed: users_table.username" in str(error.orig)
            ):
                raise UsernameAlreadyExists from None
            raise
        return self._to_profile(user)

    @staticmethod
    def _to_profile(user: User) -> UserProfile:
        return UserProfile(
            id=user.id,
            username=user.username,
            additional_info=UserAdditionalInfo(name=user.info.name),
            created_at=user.created_at,
            updated_at=max(user.updated_at, user.info.updated_at),
        )

    async def get_profile(self, user_id: UUID) -> UserProfile | None:
        user = await self.session.scalar(
            select(User)
            .options(selectinload(User.info))
            .where(User.id == user_id)
            .execution_options(populate_existing=True)
        )
        return self._to_profile(user) if user is not None else None

    async def get_credentials_by_username(
        self, username: str
    ) -> UserCredentials | None:
        row = (
            await self.session.execute(
                select(User.id, User.password_hash).where(
                    User.username == normalize_identifier(username)
                )
            )
        ).one_or_none()
        return UserCredentials(*row) if row else None

    async def get_credentials_for_update(self, user_id: UUID) -> UserCredentials | None:
        row = (
            await self.session.execute(
                select(User.id, User.password_hash)
                .where(User.id == user_id)
                .with_for_update()
            )
        ).one_or_none()
        return UserCredentials(*row) if row else None

    async def update_name(self, user_id: UUID, name: str | None) -> None:
        await self.session.execute(
            update(UserInfo).where(UserInfo.user_id == user_id).values(name=name)
        )
        await self.session.commit()

    async def update_password(self, user_id: UUID, password_hash: str) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(password_hash=password_hash)
        )
        await self.session.commit()
