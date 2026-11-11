"""Checks the pure parts of ingestion: cover detection, chunking, field
cleaning. No Gemini or DB calls (env vars below only satisfy settings)."""

import os
from pathlib import Path

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")

import pymupdf  # noqa: E402

from games_rule_core.ai.ingest import (  # noqa: E402
    GameExtract,
    clean_fields,
    parse_pdf,
    split_text,
)

TEXT = "Each player draws five cards at the start of the game.\n\n" * 10


def _png(width: int, height: int) -> bytes:
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, width, height), False)
    pix.clear_with(200)
    return bytes(pix.tobytes("png"))


def _pdf(path: Path, cover_image: bool, scanned_page: bool = False) -> Path:
    doc = pymupdf.open()
    page = doc.new_page()
    if cover_image:
        page.insert_image(page.rect, stream=_png(60, 80))
    page.insert_text((72, 72), "Rulebook")
    doc.new_page().insert_textbox(pymupdf.Rect(36, 36, 560, 800), TEXT)
    if scanned_page:  # image only, no text layer
        scan = doc.new_page()
        scan.insert_image(scan.rect, stream=_png(60, 80))
    doc.save(path)
    return path


def test_cover_page_with_full_image_is_used(tmp_path: Path) -> None:
    parsed = parse_pdf(_pdf(tmp_path / "a.pdf", cover_image=True), 0.5)
    assert parsed.cover_png is not None and parsed.cover_png[:4] == b"\x89PNG"


def test_text_only_cover_needs_generation(tmp_path: Path) -> None:
    parsed = parse_pdf(_pdf(tmp_path / "b.pdf", cover_image=False), 0.5)
    assert parsed.cover_png is None


def test_chunks_and_scanned_pages(tmp_path: Path) -> None:
    parsed = parse_pdf(_pdf(tmp_path / "c.pdf", False, scanned_page=True), 0.5)
    assert {page for page, _ in parsed.chunks} == {2}  # page 1 text is too short
    assert [page for page, _ in parsed.scanned] == [3]


def test_split_text_respects_limit() -> None:
    pieces = split_text("a" * 50 + "\n\n" + "b" * 30 + "\n\n" + "c" * 120, limit=100)
    assert all(len(p) <= 100 for p in pieces)
    assert "".join(pieces).replace("\n", "") == "a" * 50 + "b" * 30 + "c" * 120


def test_clean_fields_drops_values_that_break_constraints() -> None:
    extract = GameExtract.model_validate(
        {
            **{k: None for k in GameExtract.model_fields},
            **{
                k: []
                for k, f in GameExtract.model_fields.items()
                if "list" in str(f.annotation)
            },
            "name": "  Catan  ",
            "min_players": 3,
            "max_players": 2,
            "min_age": 0,
            "complexity_rating": 7.5,
        }
    )
    d = clean_fields(extract)
    assert d["name"] == "Catan"
    assert d["min_players"] == 3 and d["max_players"] is None
    assert d["min_age"] is None and d["complexity_rating"] is None
