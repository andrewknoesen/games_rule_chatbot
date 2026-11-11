"""Embeddings and pgvector search over rule_chunks (raw SQL: the vector is
passed as its text form and cast, so no driver codec is needed)."""

from typing import Any, Sequence

from google.genai import types
from sqlalchemy import text

from games_rule_core.ai.config import EMBED_DIM, client, settings
from games_rule_core.postgres.session import async_session_maker

_BATCH = 100  # embed_content inputs per request


def _vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(f"{v:.7g}" for v in values) + "]"


async def embed(texts: list[str], task_type: str) -> list[list[float]]:
    """task_type: RETRIEVAL_DOCUMENT for chunks, RETRIEVAL_QUERY for questions."""
    out: list[list[float]] = []
    for i in range(0, len(texts), _BATCH):
        resp = await client().aio.models.embed_content(
            model=settings.embed_model,
            contents=texts[i : i + _BATCH],
            config=types.EmbedContentConfig(
                task_type=task_type, output_dimensionality=EMBED_DIM
            ),
        )
        out.extend(list(e.values or []) for e in resp.embeddings or [])
    if len(out) != len(texts):
        raise RuntimeError(f"embedding returned {len(out)} vectors for {len(texts)}")
    return out


async def store_chunks(game_id: int, chunks: list[tuple[int, str]]) -> None:
    vectors = await embed([c for _, c in chunks], "RETRIEVAL_DOCUMENT")
    async with async_session_maker() as session:
        await session.execute(
            text(
                "INSERT INTO rule_chunks (game_id, page, content, embedding) "
                "VALUES (:game_id, :page, :content, CAST(:embedding AS vector))"
            ),
            [
                {
                    "game_id": game_id,
                    "page": page,
                    "content": content,
                    "embedding": _vector_literal(vec),
                }
                for (page, content), vec in zip(chunks, vectors)
            ],
        )
        await session.commit()


async def search_chunks(game_id: int, query: str, k: int = 6) -> list[dict[str, Any]]:
    [vec] = await embed([query], "RETRIEVAL_QUERY")
    async with async_session_maker() as session:
        rows = await session.execute(
            text(
                "SELECT page, content FROM rule_chunks WHERE game_id = :game_id "
                "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k"
            ),
            {"game_id": game_id, "q": _vector_literal(vec), "k": k},
        )
        return [{"page": r.page, "content": r.content} for r in rows]
