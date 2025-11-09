from typing import List

from fastapi import APIRouter

from rules_api.models.game import (
    Game,
    GameFactory,
    GameWithRulebooks,
    Rulebook,
    RulebookFactory,
)

router = APIRouter()


@router.post("/games/", response_model=Game)
async def create_game(game: Game) -> Game:
    # Here, `game` is already validated by Pydantic
    # Insert into database
    return game  # Should be actual DB result object


@router.get("/games/", response_model=List[Game])
async def get_games() -> list[Game]:
    # Fetch games from database
    games: List[Game] = [
        GameFactory.build(id=i) for i in range(5)
    ]  # Replace with actual DB code
    return games


@router.get("/games/{game_id}", response_model=Game)
async def get_game(game_id: int) -> Game:
    # Fetch game from DB
    game: Game = GameFactory.build(id=game_id)  # Fetch Game
    return game


@router.get("/games/{game_id}/rulebooks", response_model=GameWithRulebooks)
async def get_game_with_rulebooks(game_id: int) -> GameWithRulebooks:
    # Fetch game and related rulebooks from DB
    game: Game = GameFactory.build(id=game_id)  # Fetch Game
    rulebooks: List[Rulebook] = [RulebookFactory.build(id=game.id)]
    return GameWithRulebooks(**game.model_dump(), rulebooks=rulebooks)
