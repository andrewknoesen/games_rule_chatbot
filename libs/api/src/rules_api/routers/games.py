from typing import List, Sequence

from fastapi import APIRouter, Depends, HTTPException
from postgres.models.models import Game, Rulebook  # type: ignore
from postgres.reader.reader import PostgresReader  # type: ignore
from postgres.session import get_async_session  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/games/", response_model=Game)
async def create_game(
    game: Game, session: AsyncSession = Depends(get_async_session)
) -> Game:
    # insert game
    reader: PostgresReader[Game] = PostgresReader[Game](session, Game)
    return await reader.create(game)


@router.get("/games/", response_model=List[Game])
async def get_games(
    session: AsyncSession = Depends(get_async_session),
) -> Sequence[Game] | None:
    # Fetch games from database
    reader: PostgresReader[Game] = PostgresReader[Game](session, Game)
    game: Sequence[Game] | None = await reader.get_all()
    return game  # Automatic Pydantic serialization


@router.get("/games/{game_id}", response_model=Game)
async def get_game(
    game_id: int, session: AsyncSession = Depends(get_async_session)
) -> Game:
    # Fetch game from DB
    reader: PostgresReader[Game] = PostgresReader[Game](session, Game)
    game: Game | None = await reader.get_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game  # Automatic Pydantic serialization


@router.get("/games/{game_id}/rulebooks", response_model=List[Rulebook])
async def get_game_with_rulebooks(
    game_id: int, session: AsyncSession = Depends(get_async_session)
) -> List[Rulebook]:
    # Fetch game with eager-loaded rulebooks using selectinload
    game_reader: PostgresReader[Game] = PostgresReader[Game](session, Game)
    game: Game | None = await game_reader.get_with_relations(game_id, "rulebooks")

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return list(game.rulebooks)
