"""Find a game's official rulebook PDF on the web and fetch it safely.

Gemini with Google Search suggests PDF links; the server downloads the first
one that passes the checks below and keeps it as a "candidate" until the
user confirms it (POST /games/from-bgg) or it expires."""

import asyncio
import ipaddress
import json
import logging
import re
import shutil
import socket
import time
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urljoin, urlsplit

import httpx
import pymupdf
from google.genai import types

from games_rule_core.ai.config import client, data_path, settings
from games_rule_core.ai.ingest import render_png

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 50 * 1024 * 1024
MAX_REDIRECTS = 4
MAX_TRIES = 5  # candidate links downloaded before giving up
CANDIDATE_TTL_S = 24 * 3600
CANDIDATE_ID = re.compile(r"^[0-9a-f]{32}$")
URL_RE = re.compile(r"https://[^\s<>\"'`)\]]+")

FIND_PROMPT = """Find the official rulebook PDF for the board game "{name}"{year}{publishers}.
Search the web. Prefer the publisher's own website, then other well-known hosts.
Skip boardgamegeek.com (its files need a login), fan-made summaries, FAQs,
player aids and other languages unless no English rulebook exists.
Reply with up to 3 direct links to PDF files, best first, one per line, and
nothing else. If you find none, reply NONE."""


class UnsafeUrl(ValueError):
    pass


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in URL_RE.findall(text):
        url = match.rstrip(".,;:")
        host = urlsplit(url).hostname or ""
        if url not in urls and not host.endswith("boardgamegeek.com"):
            urls.append(url)
    return urls


def public_address(addr: str) -> bool:
    """True only for internet addresses: never loopback, LAN, link-local,
    CGNAT (tailnet), multicast or reserved ranges."""
    return ipaddress.ip_address(addr.split("%")[0]).is_global


async def _check_host(host: str) -> None:
    infos = await asyncio.get_running_loop().getaddrinfo(
        host, 443, type=socket.SOCK_STREAM
    )
    addrs = {str(info[4][0]) for info in infos}
    if not addrs or not all(public_address(a) for a in addrs):
        raise UnsafeUrl(f"{host} is not a public internet host")


async def download_pdf(url: str) -> tuple[bytes, str]:
    """(PDF bytes, final URL). https only, public hosts only (checked again
    on every redirect), at most 50 MB, and it must really be a PDF."""
    # ponytail: the host is resolved for the check and again by httpx, so a
    # DNS-rebinding host could slip through; pin the IP if this is ever
    # exposed beyond the LAN.
    async with httpx.AsyncClient(
        timeout=30, headers={"User-Agent": "games-rule-chatbot/1.0"}
    ) as http:
        for _ in range(MAX_REDIRECTS + 1):
            parts = urlsplit(url)
            if parts.scheme != "https" or not parts.hostname:
                raise UnsafeUrl(f"not an https link: {url}")
            await _check_host(parts.hostname)
            async with http.stream("GET", url) as resp:
                if resp.is_redirect:
                    url = urljoin(url, resp.headers.get("location", ""))
                    continue
                resp.raise_for_status()
                buf = bytearray()
                async for chunk in resp.aiter_bytes():
                    buf += chunk
                    if len(buf) > MAX_PDF_BYTES:
                        raise ValueError("over 50 MB")
                    if len(buf) >= 5 and not buf.startswith(b"%PDF-"):
                        raise ValueError("not a PDF")
                if not buf.startswith(b"%PDF-"):
                    raise ValueError("not a PDF")
                return bytes(buf), url
    raise ValueError("too many redirects")


def inspect_pdf(data: bytes) -> tuple[int, bytes]:
    """(page count, page-1 preview PNG); raises if PyMuPDF can't read it."""
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        if not len(doc):
            raise ValueError("PDF has no pages")
        return len(doc), render_png(doc[0], 600)


async def find_rulebook_urls(game: dict[str, Any]) -> list[str]:
    prompt = FIND_PROMPT.format(
        name=game["name"],
        year=f" ({game['year']})" if game.get("year") else "",
        publishers=(
            f", published by {', '.join(game['publishers'])}"
            if game.get("publishers")
            else ""
        ),
    )
    resp = await client().aio.models.generate_content(
        model=settings.chat_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )
    urls = extract_urls(resp.text or "")
    # The pages Search grounded on, as redirect links; usually HTML, so they
    # only help when the model's own links fail.
    for cand in resp.candidates or []:
        meta = cand.grounding_metadata
        for chunk in (meta.grounding_chunks if meta else None) or []:
            if chunk.web and chunk.web.uri and chunk.web.uri not in urls:
                urls.append(chunk.web.uri)
    return urls


def _candidate_dir(candidate_id: str) -> Path:
    if not CANDIDATE_ID.match(candidate_id):
        raise ValueError("bad candidate id")
    return data_path(f"candidates/{candidate_id}")


def load_candidate(candidate_id: str) -> Optional[dict[str, Any]]:
    try:
        folder = _candidate_dir(candidate_id)
    except ValueError:
        return None
    meta = folder / "meta.json"
    if not meta.exists():
        return None
    info: dict[str, Any] = json.loads(meta.read_text())
    info["pdf_path"] = folder / "rulebook.pdf"
    info["preview_path"] = folder / "preview.png"
    return info


def drop_candidate(candidate_id: str) -> None:
    shutil.rmtree(_candidate_dir(candidate_id), ignore_errors=True)


def _expire_candidates() -> None:
    root = data_path("candidates")
    if not root.exists():
        return
    cutoff = time.time() - CANDIDATE_TTL_S
    for folder in root.iterdir():
        if folder.stat().st_mtime < cutoff:
            shutil.rmtree(folder, ignore_errors=True)


async def find_rulebook(game: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Search, download and keep the first rulebook that passes the checks.
    Returns the candidate's public details, or None when nothing passed."""
    _expire_candidates()
    for url in (await find_rulebook_urls(game))[:MAX_TRIES]:
        try:
            data, final_url = await download_pdf(url)
            pages, preview = await asyncio.to_thread(inspect_pdf, data)
        except Exception as exc:
            logger.info("rulebook candidate rejected (%s): %s", exc, url)
            continue
        candidate_id = uuid.uuid4().hex
        folder = _candidate_dir(candidate_id)
        folder.mkdir(parents=True)
        (folder / "rulebook.pdf").write_bytes(data)
        (folder / "preview.png").write_bytes(preview)
        name = unquote(urlsplit(final_url).path.rsplit("/", 1)[-1]) or "rulebook.pdf"
        info = {
            "id": candidate_id,
            "bgg_id": game["id"],
            "source_url": final_url,
            "host": urlsplit(final_url).hostname,
            "file_name": name[:255],
            "pages": pages,
            "size_bytes": len(data),
        }
        (folder / "meta.json").write_text(json.dumps(info))
        return info
    return None
