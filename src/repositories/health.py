from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.database import engine


async def is_database_available() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True
