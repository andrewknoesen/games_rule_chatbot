from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from games_rule_core.postgres.models.models import Game
from games_rule_core.postgres.session import async_session_maker
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from games_rule_api.exceptions.exceptions import integrity_error_handler
from games_rule_api.routers import games, health, settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Ingestion runs in-process, so anything still "processing" at startup
    # was cut off by a restart.
    async with async_session_maker() as session:
        await session.execute(
            update(Game)
            .where(Game.status == "processing")  # type: ignore[arg-type]
            .values(status="failed", error="Interrupted by a restart; upload again.")
        )
        await session.commit()
    yield


app = FastAPI(title="Games Rule API", lifespan=lifespan)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.include_router(games.router)
app.include_router(settings.router)
app.include_router(health.router)
