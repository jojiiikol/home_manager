from fastapi import Request
from fastapi.responses import JSONResponse

from src.exceptions.houses import (
    AlreadyHouseParticipant,
    HouseAccessDenied,
    HouseError,
    HouseLoginAlreadyExists,
    HouseNotFound,
    IncorrectHousePassword,
    InvalidHouseCredentials,
    InvalidParticipantTransition,
    LastActiveAdmin,
    ParticipantNotFound,
)

HOUSE_ERRORS = {
    HouseNotFound: (404, "House not found"),
    HouseAccessDenied: (403, "House access denied"),
    HouseLoginAlreadyExists: (409, "House login already exists"),
    InvalidHouseCredentials: (400, "Invalid house login or password"),
    AlreadyHouseParticipant: (409, "Already a house participant"),
    ParticipantNotFound: (404, "Participant not found"),
    LastActiveAdmin: (409, "House must have at least one active admin"),
    InvalidParticipantTransition: (
        409,
        "Restore participant first; change role separately",
    ),
    IncorrectHousePassword: (400, "Incorrect old house password"),
}


async def house_error_handler(request: Request, error: HouseError) -> JSONResponse:
    status_code, detail = HOUSE_ERRORS[type(error)]
    return JSONResponse(status_code=status_code, content={"detail": detail})
