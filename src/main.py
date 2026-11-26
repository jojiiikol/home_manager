from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings
from src.database import engine
from src.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.include_router(router)
