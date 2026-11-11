import shutil
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from games_rule_core.ai.agent import ask
from games_rule_core.ai.config import data_path
from games_rule_core.ai.ingest import ingest_game
from games_rule_core.postgres.models.models import Game, GameDocument
from games_rule_core.postgres.session import get_async_session
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

router = APIRouter(tags=["games"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
# Heavy JSON columns left out of the list view.
DETAIL_ONLY = {
    "components",
    "setup",
    "turn_structure",
    "rules",
    "win_conditions",
    "special_rules",
    "glossary",
}


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


async def _game_or_404(session: AsyncSession, game_id: int) -> Game:
    game = await session.get(Game, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    return game


@router.get("/games")
async def list_games(
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, Any]]:
    games = (
        await session.execute(select(Game).order_by(Game.created_at.desc()))  # type: ignore[union-attr]
    ).scalars()
    return [g.model_dump(exclude=DETAIL_ONLY) for g in games]


@router.post("/games/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_rulebook(
    file: UploadFile,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Store a rulebook PDF and start ingestion. Poll GET /games/{id} until
    status is ready or failed."""
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "PDF is over 50 MB")
    if not data.startswith(b"%PDF"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a PDF rulebook"
        )

    file_name = (file.filename or "rulebook.pdf")[:255]
    # Placeholder name until extraction finds the real one.
    game = Game(name=file_name.rsplit(".", 1)[0] or "New game")
    session.add(game)
    await session.flush()
    if game.id is None:  # flush always assigns it; narrows the type
        raise RuntimeError("game id not assigned")

    rel = f"games/{game.id}/rulebook.pdf"
    path = data_path(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    session.add(
        GameDocument(
            game_id=game.id,
            document_type="rulebook",
            file_path=rel,
            file_name=file_name,
            file_size_bytes=len(data),
            mime_type="application/pdf",
        )
    )
    await session.commit()

    # ponytail: in-process background task; a restart loses the job (the
    # startup hook marks it failed). Add a worker if uploads get frequent.
    background.add_task(ingest_game, game.id)
    return {"id": game.id, "status": game.status}


@router.get("/games/{game_id}", response_model=Game)
async def get_game(
    game_id: int, session: AsyncSession = Depends(get_async_session)
) -> Game:
    return await _game_or_404(session, game_id)


@router.get("/games/{game_id}/cover")
async def get_cover(
    game_id: int, session: AsyncSession = Depends(get_async_session)
) -> FileResponse:
    game = await _game_or_404(session, game_id)
    if not game.cover_path or not data_path(game.cover_path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No cover image")
    # Content type follows the file extension (.png render or .jpg generated).
    return FileResponse(data_path(game.cover_path))


@router.get("/games/{game_id}/rulebook")
async def get_rulebook(
    game_id: int, session: AsyncSession = Depends(get_async_session)
) -> FileResponse:
    doc = (
        await session.execute(
            select(GameDocument).where(
                col(GameDocument.game_id) == game_id,
                col(GameDocument.document_type) == "rulebook",
            )
        )
    ).scalar_one_or_none()
    if doc is None or not data_path(doc.file_path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No rulebook")
    return FileResponse(
        data_path(doc.file_path), media_type="application/pdf", filename=doc.file_name
    )


@router.delete("/games/{game_id}")
async def delete_game(
    game_id: int, session: AsyncSession = Depends(get_async_session)
) -> dict[str, int]:
    await _game_or_404(session, game_id)
    # Documents and rule chunks go with it (ON DELETE CASCADE).
    await session.execute(delete(Game).where(Game.id == game_id))  # type: ignore[arg-type]
    await session.commit()
    shutil.rmtree(data_path(f"games/{game_id}"), ignore_errors=True)
    return {"deleted": game_id}


@router.post("/games/{game_id}/ask")
async def ask_judge(
    game_id: int,
    body: Question,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    game = await _game_or_404(session, game_id)
    if game.status != "ready":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Rulebook is {game.status}, not ready"
        )
    try:
        return {"answer": await ask(game_id, body.question)}
    except Exception as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Rules judge failed: {exc}"
        ) from exc
