from src.dto.health import ReadinessResult
from src.repositories.health import is_database_available


async def check_readiness() -> ReadinessResult:
    return ReadinessResult(database_available=await is_database_available())
