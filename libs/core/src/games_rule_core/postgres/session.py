# libs/storage/src/games_rule_storage/session.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings  # Import the settings instance

# Use settings.database_url to create the engine
async_engine = create_async_engine(
    settings.database_url,  # This reads from your Settings Pydantic model
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield database sessions for FastAPI dependency injection."""
    async with async_session_maker() as session:
        yield session
