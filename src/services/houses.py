from uuid import UUID

from anyio import to_thread

from src.domain.houses import ParticipantRole, ParticipantStatus
from src.dto.houses import HouseCredentials, HouseProfile, Participant
from src.exceptions.houses import (
    AlreadyHouseParticipant,
    HouseAccessDenied,
    HouseNotFound,
    IncorrectHousePassword,
    InvalidHouseCredentials,
    InvalidParticipantTransition,
    LastActiveAdmin,
    ParticipantNotFound,
)
from src.repositories.houses import HousesRepository
from src.security.passwords import dummy_hash, hash_password, verify_password


class HousesService:
    def __init__(self, repository: HousesRepository):
        self.repository = repository

    async def create(
        self, user_id: UUID, login: str, password: str, name: str
    ) -> HouseProfile:
        password_hash = await to_thread.run_sync(hash_password, password)
        return await self.repository.create(login, password_hash, name, user_id)

    async def _lock_house(self, house_id: UUID) -> HouseCredentials:
        house = await self.repository.lock_house(house_id)
        if house is None:
            raise HouseNotFound
        return house

    async def _require_member(
        self,
        house_id: UUID,
        user_id: UUID,
        *,
        active: bool = False,
        admin: bool = False,
    ) -> Participant:
        participant = await self.repository.get_participant(house_id, user_id)
        if participant is None:
            raise HouseAccessDenied
        if (active or admin) and participant.status != ParticipantStatus.ACTIVE:
            raise HouseAccessDenied
        if admin and participant.role != ParticipantRole.ADMIN:
            raise HouseAccessDenied
        return participant

    async def get_profile(self, house_id: UUID, user_id: UUID) -> HouseProfile:
        await self._require_member(house_id, user_id)
        house = await self.repository.get_profile(house_id)
        if house is None:
            raise HouseNotFound
        return house

    async def list_houses(self, user_id: UUID) -> list[HouseProfile]:
        return await self.repository.list_for_user(user_id)

    async def get_my_participation(self, house_id: UUID, user_id: UUID) -> Participant:
        return await self._require_member(house_id, user_id)

    async def list_participants(
        self, house_id: UUID, user_id: UUID
    ) -> list[Participant]:
        await self._require_member(house_id, user_id, active=True)
        return await self.repository.list_participants(house_id)

    async def join(self, user_id: UUID, login: str, password: str) -> Participant:
        house = await self.repository.lock_house_by_login(login)
        valid = await to_thread.run_sync(
            verify_password, password, house.password_hash if house else dummy_hash
        )
        if not house or not valid:
            raise InvalidHouseCredentials
        participant = await self.repository.get_participant(house.id, user_id)
        if participant:
            if participant.status == ParticipantStatus.ACTIVE:
                raise AlreadyHouseParticipant
            if participant.status == ParticipantStatus.BLOCKED:
                raise HouseAccessDenied
            await self.repository.update_participant(
                participant.id, ParticipantRole.MEMBER, ParticipantStatus.ACTIVE
            )
        else:
            await self.repository.add_participant(house.id, user_id)
        await self.repository.commit()
        return await self._require_member(house.id, user_id)

    async def update_profile(
        self, house_id: UUID, user_id: UUID, login: str | None, name: str | None
    ) -> HouseProfile:
        await self._lock_house(house_id)
        await self._require_member(house_id, user_id, admin=True)
        await self.repository.update_profile(house_id, login, name)
        await self.repository.commit()
        return await self.get_profile(house_id, user_id)

    async def change_password(
        self, house_id: UUID, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        house = await self._lock_house(house_id)
        await self._require_member(house_id, user_id, admin=True)
        if not await to_thread.run_sync(
            verify_password, old_password, house.password_hash
        ):
            raise IncorrectHousePassword
        password_hash = await to_thread.run_sync(hash_password, new_password)
        await self.repository.update_password(house_id, password_hash)
        await self.repository.commit()

    async def _protect_last_admin(
        self,
        house_id: UUID,
        participant: Participant,
        role: ParticipantRole,
        status: ParticipantStatus,
    ) -> None:
        was_active_admin = (
            participant.role == ParticipantRole.ADMIN
            and participant.status == ParticipantStatus.ACTIVE
        )
        remains_active_admin = (
            role == ParticipantRole.ADMIN and status == ParticipantStatus.ACTIVE
        )
        if was_active_admin and not remains_active_admin:
            if await self.repository.count_active_admins(house_id) <= 1:
                raise LastActiveAdmin

    async def leave(self, house_id: UUID, user_id: UUID) -> Participant:
        await self._lock_house(house_id)
        participant = await self._require_member(house_id, user_id, active=True)
        await self._protect_last_admin(
            house_id, participant, participant.role, ParticipantStatus.LEFT
        )
        await self.repository.update_participant(
            participant.id, participant.role, ParticipantStatus.LEFT
        )
        await self.repository.commit()
        return await self._require_member(house_id, user_id)

    async def update_participant(
        self,
        house_id: UUID,
        actor_id: UUID,
        target_user_id: UUID,
        role: ParticipantRole | None,
        status: ParticipantStatus | None,
    ) -> Participant:
        # Единая блокировка дома сериализует вступление, выход и смену прав.
        await self._lock_house(house_id)
        await self._require_member(house_id, actor_id, admin=True)
        target = await self.repository.get_participant(house_id, target_user_id)
        if target is None:
            raise ParticipantNotFound
        new_role = role if role is not None else target.role
        new_status = status if status is not None else target.status
        if (
            target.status != ParticipantStatus.ACTIVE
            and new_status == ParticipantStatus.ACTIVE
        ):
            if role is not None:
                raise InvalidParticipantTransition
            new_role = ParticipantRole.MEMBER
        await self._protect_last_admin(house_id, target, new_role, new_status)
        await self.repository.update_participant(target.id, new_role, new_status)
        await self.repository.commit()
        return await self._require_member(house_id, target_user_id)
