from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.houses import ParticipantRole, ParticipantStatus
from src.dto.houses import (
    HouseAdditionalInfo,
    HouseCredentials,
    HouseProfile,
    Participant,
)
from src.exceptions.houses import HouseLoginAlreadyExists
from src.models.houses import House, HouseInfo, HouseParticipant


class HousesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self._raise_integrity_error(error)

    async def _raise_integrity_error(self, error: IntegrityError) -> None:
        await self.session.rollback()
        constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_houses_table_login" or (
            self.session.bind.dialect.name == "sqlite"
            and "UNIQUE constraint failed: houses_table.login" in str(error.orig)
        ):
            raise HouseLoginAlreadyExists from None
        raise error

    async def create(
        self, login: str, password_hash: str, name: str, user_id: UUID
    ) -> HouseProfile:
        house = House(
            login=login,
            password_hash=password_hash,
            info=HouseInfo(name=name),
            participants=[
                HouseParticipant(
                    user_id=user_id,
                    role=ParticipantRole.ADMIN,
                    status=ParticipantStatus.ACTIVE,
                )
            ],
        )
        self.session.add(house)
        await self.commit()
        return self._house_profile(house)

    @staticmethod
    def _house_profile(house: House) -> HouseProfile:
        return HouseProfile(
            id=house.id,
            login=house.login,
            additional_info=HouseAdditionalInfo(name=house.info.name),
            created_at=house.created_at,
            updated_at=max(house.updated_at, house.info.updated_at),
        )

    @staticmethod
    def _participant(participant: HouseParticipant) -> Participant:
        return Participant(
            id=participant.id,
            house_id=participant.house_id,
            user_id=participant.user_id,
            role=participant.role,
            status=participant.status,
            created_at=participant.created_at,
            updated_at=participant.updated_at,
        )

    async def lock_house(self, house_id: UUID) -> HouseCredentials | None:
        row = (
            await self.session.execute(
                select(House.id, House.password_hash)
                .where(House.id == house_id)
                .with_for_update()
            )
        ).one_or_none()
        return HouseCredentials(*row) if row else None

    async def lock_house_by_login(self, login: str) -> HouseCredentials | None:
        row = (
            await self.session.execute(
                select(House.id, House.password_hash)
                .where(House.login == login)
                .with_for_update()
            )
        ).one_or_none()
        return HouseCredentials(*row) if row else None

    async def get_profile(self, house_id: UUID) -> HouseProfile | None:
        house = await self.session.scalar(
            select(House)
            .options(selectinload(House.info))
            .where(House.id == house_id)
            .execution_options(populate_existing=True)
        )
        return self._house_profile(house) if house else None

    async def list_for_user(self, user_id: UUID) -> list[HouseProfile]:
        houses = await self.session.scalars(
            select(House)
            .join(HouseParticipant)
            .options(selectinload(House.info))
            .where(HouseParticipant.user_id == user_id)
            .order_by(House.created_at, House.id)
        )
        return [self._house_profile(house) for house in houses]

    async def get_participant(
        self, house_id: UUID, user_id: UUID
    ) -> Participant | None:
        participant = await self.session.scalar(
            select(HouseParticipant)
            .where(
                HouseParticipant.house_id == house_id,
                HouseParticipant.user_id == user_id,
            )
            .execution_options(populate_existing=True)
        )
        return self._participant(participant) if participant else None

    async def list_participants(self, house_id: UUID) -> list[Participant]:
        participants = await self.session.scalars(
            select(HouseParticipant)
            .where(HouseParticipant.house_id == house_id)
            .order_by(HouseParticipant.created_at, HouseParticipant.id)
        )
        return [self._participant(participant) for participant in participants]

    async def count_active_admins(self, house_id: UUID) -> int:
        return await self.session.scalar(
            select(func.count())
            .select_from(HouseParticipant)
            .where(
                HouseParticipant.house_id == house_id,
                HouseParticipant.role == ParticipantRole.ADMIN,
                HouseParticipant.status == ParticipantStatus.ACTIVE,
            )
        )

    async def add_participant(self, house_id: UUID, user_id: UUID) -> None:
        self.session.add(
            HouseParticipant(
                house_id=house_id,
                user_id=user_id,
                role=ParticipantRole.MEMBER,
                status=ParticipantStatus.ACTIVE,
            )
        )

    async def update_participant(
        self, participant_id: UUID, role: ParticipantRole, status: ParticipantStatus
    ) -> None:
        await self.session.execute(
            update(HouseParticipant)
            .where(HouseParticipant.id == participant_id)
            .values(role=role, status=status, updated_at=func.now())
        )

    async def update_profile(
        self, house_id: UUID, login: str | None, name: str | None
    ) -> None:
        if login is not None:
            try:
                await self.session.execute(
                    update(House).where(House.id == house_id).values(login=login)
                )
            except IntegrityError as error:
                await self._raise_integrity_error(error)
        if name is not None:
            await self.session.execute(
                update(HouseInfo)
                .where(HouseInfo.house_id == house_id)
                .values(name=name)
            )

    async def update_password(self, house_id: UUID, password_hash: str) -> None:
        await self.session.execute(
            update(House)
            .where(House.id == house_id)
            .values(password_hash=password_hash)
        )
