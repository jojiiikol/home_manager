from fastapi import APIRouter, HTTPException, status

from src.schemas.health import HealthResponse
from src.services.health import check_readiness

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"description": "Database unavailable"}},
)
async def readiness() -> HealthResponse:
    result = await check_readiness()
    if not result.database_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )
    return HealthResponse(status="ok")
