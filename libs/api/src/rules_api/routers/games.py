from fastapi import APIRouter

router = APIRouter()


@router.get("/games")
def get_games() -> dict[str, list[str]]:
    return {"games": ["chess", "checkers", "go"]}
