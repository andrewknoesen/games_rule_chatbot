"""Rulebook ingestion: PDF -> structured game fields, RAG chunks, cover image.

Runs as a background task after upload; the game row goes processing ->
ready | failed. The PDF parsing helpers are pure so they can be tested
without Gemini (see libs/core/tests/test_ingest.py)."""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pymupdf
from google.genai import types
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlmodel import col

from games_rule_core.ai.bgg import find_cover
from games_rule_core.ai.config import client, data_path, settings
from games_rule_core.ai.rag import store_chunks
from games_rule_core.postgres.models.models import Game, GameDocument
from games_rule_core.postgres.session import async_session_maker

logger = logging.getLogger(__name__)

CHUNK_CHARS = 1500
MIN_PAGE_TEXT = 20  # fewer chars than this = a scanned page with no text layer
COVER_WIDTH_PX = 800


# --- Structured extraction schema (shapes match the frontend detail page) ---


class Component(BaseModel):
    name: str
    quantity: Optional[int]
    description: Optional[str]


class SetupStep(BaseModel):
    instruction: str


class TurnPhase(BaseModel):
    phase: str
    description: str


class Rule(BaseModel):
    category: str
    title: str
    description: str


class WinCondition(BaseModel):
    condition: str


class GlossaryTerm(BaseModel):
    term: str
    definition: str


class GameExtract(BaseModel):
    name: str
    description: Optional[str]
    objective: Optional[str]
    game_types: list[str]
    game_mechanics: list[str]
    min_players: Optional[int]
    max_players: Optional[int]
    min_playtime_minutes: Optional[int]
    max_playtime_minutes: Optional[int]
    min_age: Optional[int]
    complexity_rating: Optional[float]
    year_published: Optional[int]
    publisher: Optional[str]
    designer: Optional[str]
    components: list[Component]
    setup: list[SetupStep]
    turn_structure: list[TurnPhase]
    rules: list[Rule]
    win_conditions: list[WinCondition]
    special_rules: list[Rule]
    glossary: list[GlossaryTerm]


EXTRACT_PROMPT = """You are reading the complete rulebook of a tabletop game.
Fill in every field from the rulebook only; never guess from outside knowledge.
Use null (or an empty list) when the rulebook does not say.
- objective: one or two sentences on how a player wins / what they try to do.
- setup: ordered steps. turn_structure: ordered phases of one turn.
- rules: the core rules grouped by category (e.g. Movement, Combat, Scoring).
- special_rules: exceptions, variants, edge cases, advanced or solo rules.
- complexity_rating: 1.0 (very light) to 5.0 (very heavy), your estimate.
- Keep every description concise and faithful to the rulebook wording."""


def clean_fields(extract: GameExtract) -> dict[str, Any]:
    """Model output -> games row values, nulling numbers that would break the
    table's CHECK constraints instead of failing the whole ingestion."""
    d = extract.model_dump()
    for key in (
        "min_players",
        "max_players",
        "min_playtime_minutes",
        "max_playtime_minutes",
        "min_age",
    ):
        if d[key] is not None and d[key] <= 0:
            d[key] = None
    for lo, hi in (
        ("min_players", "max_players"),
        ("min_playtime_minutes", "max_playtime_minutes"),
    ):
        if d[lo] is not None and d[hi] is not None and d[hi] < d[lo]:
            d[hi] = None
    if d["complexity_rating"] is not None and not 1 <= d["complexity_rating"] <= 5:
        d["complexity_rating"] = None
    d["name"] = (d["name"] or "").strip()[:255] or None
    return d


# --- PDF parsing (pure, sync; run in a thread) ---


@dataclass
class ParsedPdf:
    chunks: list[tuple[int, str]] = field(default_factory=list)  # (page, text)
    scanned: list[tuple[int, bytes]] = field(default_factory=list)  # (page, png)
    cover_png: Optional[bytes] = None  # page 1 render, if it looks like a cover


def split_text(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    """Split on paragraph breaks into pieces of at most `limit` chars."""
    pieces: list[str] = []
    current = ""
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        while len(para) > limit:  # a single huge paragraph: hard split
            if current:
                pieces.append(current)
                current = ""
            pieces.append(para[:limit])
            para = para[limit:]
        if current and len(current) + 2 + len(para) > limit:
            pieces.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        pieces.append(current)
    return pieces


def image_coverage(page: pymupdf.Page) -> float:
    """Share of the page area covered by raster images (0..1)."""
    page_rect = page.rect
    covered = 0.0
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"]) & page_rect
        if not r.is_empty:
            covered += r.width * r.height
    # ponytail: overlapping images double-count; capped at 1, fine for a
    # cover-or-not threshold.
    return min(1.0, float(covered / (page_rect.width * page_rect.height)))


def render_png(page: pymupdf.Page, width: int = COVER_WIDTH_PX) -> bytes:
    zoom = width / page.rect.width
    return bytes(page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png"))


def parse_pdf(path: Path, cover_min_ratio: float) -> ParsedPdf:
    parsed = ParsedPdf()
    with pymupdf.open(path) as doc:
        for index, page in enumerate(doc):
            page_no = index + 1
            text = page.get_text().strip()
            if len(text) < MIN_PAGE_TEXT:
                if page.get_image_info():
                    parsed.scanned.append((page_no, render_png(page, 1200)))
            else:
                parsed.chunks.extend((page_no, c) for c in split_text(text))
        if len(doc) and image_coverage(doc[0]) >= cover_min_ratio:
            parsed.cover_png = render_png(doc[0])
    return parsed


# --- Gemini calls ---


async def extract_fields(pdf: Path) -> GameExtract:
    uploaded = await client().aio.files.upload(
        file=pdf, config=types.UploadFileConfig(mime_type="application/pdf")
    )
    try:
        resp = await client().aio.models.generate_content(
            model=settings.extract_model,
            contents=[uploaded, EXTRACT_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=GameExtract
            ),
        )
    finally:
        if uploaded.name:
            await client().aio.files.delete(name=uploaded.name)
    if isinstance(resp.parsed, GameExtract):
        return resp.parsed
    return GameExtract.model_validate_json(resp.text or "")


async def transcribe_page(png: bytes) -> str:
    resp = await client().aio.models.generate_content(
        model=settings.extract_model,
        contents=[
            types.Part.from_bytes(data=png, mime_type="image/png"),
            "Transcribe all text on this rulebook page as plain text, "
            "keeping paragraph breaks. Output only the text.",
        ],
    )
    return (resp.text or "").strip()


async def generate_cover(game: GameExtract) -> Optional[bytes]:
    components = ", ".join(c.name for c in game.components[:8])
    prompt = (
        f"Box-cover style illustration for the tabletop game '{game.name}'. "
        f"Theme: {game.description or game.objective or 'a board game'}. "
        f"Show its world and components ({components or 'cards, tokens, board'}) "
        "in a vivid, painterly board-game art style. No text, no logos."
    )
    resp = await client().aio.models.generate_content(
        model=settings.image_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="4:3"),
        ),
    )
    for part in resp.parts or []:
        if part.inline_data and part.inline_data.data:
            return part.inline_data.data
    return None


# --- Orchestration ---


def cover_name(data: bytes) -> str:
    """File name with the extension the cover route serves the type from."""
    if data[:2] == b"\xff\xd8":
        return "cover.jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "cover.webp"
    return "cover.png"


def save_cover(game: Game, folder: Path, data: bytes) -> None:
    rel = str(folder / cover_name(data))
    data_path(rel).write_bytes(data)
    if game.cover_path and game.cover_path != rel:
        data_path(game.cover_path).unlink(missing_ok=True)
    game.cover_path = rel


async def ingest_game(game_id: int) -> None:
    async with async_session_maker() as session:
        game = await session.get(Game, game_id)
        if game is None:
            return
        doc = (
            await session.execute(
                select(GameDocument).where(
                    col(GameDocument.game_id) == game_id,
                    col(GameDocument.document_type) == "rulebook",
                )
            )
        ).scalar_one()
        try:
            pdf = data_path(doc.file_path)
            parsed = await asyncio.to_thread(
                parse_pdf, pdf, settings.cover_min_image_ratio
            )
            extract = await extract_fields(pdf)

            chunks = parsed.chunks
            for page_no, png in parsed.scanned:
                chunks += [(page_no, c) for c in split_text(await transcribe_page(png))]
            if not chunks:
                raise ValueError("no readable text found in the PDF")
            await store_chunks(game_id, sorted(chunks))

            # Cover: BGG box art, else page 1 if it is a cover, else generated.
            # A missing cover must not fail the game.
            cover = None
            try:
                found = await find_cover(extract.name, extract.year_published)
                if found:
                    game.bgg_id, cover = found
            except Exception:
                logger.exception("BGG lookup failed for game %s", game_id)
            cover = cover or parsed.cover_png
            if cover is None:
                try:
                    cover = await generate_cover(extract)
                except Exception:
                    logger.exception("cover generation failed for game %s", game_id)
            if cover:
                save_cover(game, Path(doc.file_path).parent, cover)

            for key, value in clean_fields(extract).items():
                if value is not None or key != "name":
                    setattr(game, key, value)
            game.status, game.error = "ready", None
        except Exception as exc:
            logger.exception("ingestion failed for game %s", game_id)
            await session.execute(
                text("DELETE FROM rule_chunks WHERE game_id = :g"), {"g": game_id}
            )
            game.status, game.error = "failed", str(exc)[:1000]
        await session.commit()


async def backfill_bgg_covers() -> None:
    """Swap in BGG box art for ready games that have none yet. Run on the
    host after adding BGG_TOKEN:
    docker compose -f deploy/compose.yaml exec api python3 -m games_rule_core.ai.ingest
    """
    async with async_session_maker() as session:
        games = (
            await session.execute(
                select(Game).where(
                    col(Game.status) == "ready", col(Game.bgg_id).is_(None)
                )
            )
        ).scalars()
        for game in games:
            found = await find_cover(game.name, game.year_published)
            if not found:
                print(f"{game.id} {game.name}: not on BGG")
                continue
            game.bgg_id, cover = found
            if cover:
                save_cover(game, Path("games") / str(game.id), cover)
            print(f"{game.id} {game.name}: BGG {game.bgg_id}, image={bool(cover)}")
        await session.commit()


if __name__ == "__main__":
    if not settings.bgg_token:
        raise SystemExit("BGG_TOKEN is not set")
    asyncio.run(backfill_bgg_covers())
