from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.repositories.houses import HousesRepository
from src.routes.dependencies import CurrentUser
from src.schemas.houses import (
    ChangeHousePasswordRequest,
    CreateHouseRequest,
    HouseResponse,
    JoinHouseRequest,
    ParticipantResponse,
    UpdateHouseRequest,
    UpdateParticipantRequest,
)
from src.services.houses import HousesService

router = APIRouter(prefix="/houses", tags=["houses"])


def get_houses_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HousesService:
    return HousesService(HousesRepository(session))


HouseServiceDependency = Annotated[HousesService, Depends(get_houses_service)]


@router.post("", response_model=HouseResponse, status_code=status.HTTP_201_CREATED)
async def create_house(
    body: CreateHouseRequest,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> HouseResponse:
    house = await service.create(
        user.id, body.login, body.password.get_secret_value(), body.name
    )
    return HouseResponse.model_validate(house)


@router.get("", response_model=list[HouseResponse])
async def list_houses(user: CurrentUser, service: HouseServiceDependency):
    return [
        HouseResponse.model_validate(house)
        for house in await service.list_houses(user.id)
    ]


@router.post("/join", response_model=ParticipantResponse)
async def join_house(
    body: JoinHouseRequest,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> ParticipantResponse:
    participant = await service.join(
        user.id, body.login, body.password.get_secret_value()
    )
    return ParticipantResponse.model_validate(participant)


@router.get("/{house_id}", response_model=HouseResponse)
async def get_house(
    house_id: UUID,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> HouseResponse:
    return HouseResponse.model_validate(await service.get_profile(house_id, user.id))


@router.patch("/{house_id}", response_model=HouseResponse)
async def update_house(
    house_id: UUID,
    body: UpdateHouseRequest,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> HouseResponse:
    house = await service.update_profile(house_id, user.id, body.login, body.name)
    return HouseResponse.model_validate(house)


@router.put("/{house_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_house_password(
    house_id: UUID,
    body: ChangeHousePasswordRequest,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> Response:
    await service.change_password(
        house_id,
        user.id,
        body.old_password.get_secret_value(),
        body.new_password.get_secret_value(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{house_id}/participants/me", response_model=ParticipantResponse)
async def my_participation(
    house_id: UUID,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> ParticipantResponse:
    return ParticipantResponse.model_validate(
        await service.get_my_participation(house_id, user.id)
    )


@router.get("/{house_id}/participants", response_model=list[ParticipantResponse])
async def list_participants(
    house_id: UUID,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> list[ParticipantResponse]:
    return [
        ParticipantResponse.model_validate(participant)
        for participant in await service.list_participants(house_id, user.id)
    ]


@router.post("/{house_id}/leave", response_model=ParticipantResponse)
async def leave_house(
    house_id: UUID,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> ParticipantResponse:
    return ParticipantResponse.model_validate(await service.leave(house_id, user.id))


@router.patch("/{house_id}/participants/{user_id}", response_model=ParticipantResponse)
async def update_participant(
    house_id: UUID,
    user_id: UUID,
    body: UpdateParticipantRequest,
    user: CurrentUser,
    service: HouseServiceDependency,
) -> ParticipantResponse:
    return ParticipantResponse.model_validate(
        await service.update_participant(
            house_id,
            user.id,
            user_id,
            body.role,
            body.status,
        )
    )
