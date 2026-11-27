from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings
from src.database import engine
from src.exceptions.houses import HouseError
from src.routes import router
from src.routes.house_errors import house_error_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    root_path=settings.root_path,
)
app.include_router(router)
app.add_exception_handler(HouseError, house_error_handler)
