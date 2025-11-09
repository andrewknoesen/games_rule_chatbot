from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Create async engine
async_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=True,
    future=True,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=20,  # Connection pool size
    max_overflow=10,  # Additional connections if pool is full
)

# Create async session maker
async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# Dependency for FastAPI
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield database sessions for FastAPI dependency injection."""
    async with async_session_maker() as session:
        yield session
