"""BoardGameGeek's XML API2: game search, game details and box art.

Needs an approved BGG application token in BGG_TOKEN; without one, search is
unavailable and covers fall back to the rulebook or a generated image. Terms
(https://boardgamegeek.com/using_the_xml_api): non-commercial use, credit
BGG, call from the server and keep requests few, and do not modify the
data, so images are stored exactly as downloaded."""

from typing import Any, Optional
from xml.etree import ElementTree  # nosec B405 (see _parse)

import httpx

from games_rule_core.ai.config import settings

API = "https://boardgamegeek.com/xmlapi2"  # no www: tokens fail there
MAX_IMAGE_BYTES = 10 * 1024 * 1024
THING_BATCH = 20  # most ids BGG accepts in one /thing call


class BggUnavailable(RuntimeError):
    """No BGG token configured."""


def _parse(xml: str) -> ElementTree.Element:
    # BGG's own responses; the bundled expat (>= 2.4) refuses entity-expansion
    # bombs, so stdlib parsing is enough here.
    return ElementTree.fromstring(xml)  # nosec B314


def _value(item: ElementTree.Element, tag: str) -> Optional[str]:
    node = item.find(tag)
    return node.get("value") if node is not None else None


def _int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def pick_game_id(search_xml: str, year: Optional[int]) -> Optional[int]:
    """Id from an exact-name search; prefer the rulebook's publication year
    when several games share the name (reprints, remakes)."""
    ids: list[int] = []
    for item in _parse(search_xml).iter("item"):
        game_id = int(item.get("id", "0"))
        if year is not None and _value(item, "yearpublished") == str(year):
            return game_id
        ids.append(game_id)
    # ponytail: same name, no year match -> first hit; add a manual override
    # if wrong covers show up.
    return ids[0] if ids else None


def rank_search(search_xml: str, query: str, limit: int) -> list[int]:
    """Ids of the best name matches: exact, then prefix, then the rest.
    BGG returns hits in no useful order, and /thing takes 20 ids at most."""
    scored: dict[int, tuple[int, int]] = {}
    for i, item in enumerate(_parse(search_xml).iter("item")):
        game_id = int(item.get("id", "0"))
        if game_id and game_id not in scored:
            scored[game_id] = (_name_rank(_value(item, "name") or "", query), i)
    return sorted(scored, key=lambda game_id: scored[game_id])[:limit]


def _name_rank(name: str, query: str) -> int:
    n, q = name.casefold(), query.casefold().strip()
    return 0 if n == q else 1 if n.startswith(q) else 2


def parse_things(thing_xml: str) -> list[dict[str, Any]]:
    games = []
    for item in _parse(thing_xml).iter("item"):
        primary = next(
            (
                n.get("value")
                for n in item.findall("name")
                if n.get("type") == "primary"
            ),
            None,
        )
        rated = item.find("statistics/ratings/usersrated")
        games.append(
            {
                "id": int(item.get("id", "0")),
                "type": item.get("type"),
                "name": primary,
                "year": _int(_value(item, "yearpublished")),
                "thumbnail": (item.findtext("thumbnail") or "").strip() or None,
                "image": (item.findtext("image") or "").strip() or None,
                "publishers": [
                    link.get("value")
                    for link in item.findall("link")
                    if link.get("type") == "boardgamepublisher"
                ][:3],
                "users_rated": _int(rated.get("value")) if rated is not None else 0,
            }
        )
    return games


def image_url(thing_xml: str) -> Optional[str]:
    games = parse_things(thing_xml)
    url = games[0]["image"] if games else None
    return url if url and url.startswith("https://") else None


async def _get(http: httpx.AsyncClient, path: str, params: dict[str, Any]) -> str:
    if not settings.bgg_token:
        raise BggUnavailable("BGG_TOKEN is not set")
    resp = await http.get(
        f"{API}/{path}",
        params=params,
        headers={"Authorization": f"Bearer {settings.bgg_token}"},
    )
    resp.raise_for_status()
    return resp.text


async def search_games(query: str, limit: int = THING_BATCH) -> list[dict[str, Any]]:
    """Board games (no expansions) matching the query, best match first,
    most-rated first among equally good name matches."""
    async with httpx.AsyncClient(timeout=30) as http:
        ids = rank_search(
            await _get(http, "search", {"query": query, "type": "boardgame"}),
            query,
            limit,
        )
        if not ids:
            return []
        games = parse_things(
            await _get(http, "thing", {"id": ",".join(map(str, ids)), "stats": 1})
        )
    games = [g for g in games if g["type"] == "boardgame" and g["name"]]
    games.sort(key=lambda g: (_name_rank(g["name"], query), -(g["users_rated"] or 0)))
    return games


async def get_game(bgg_id: int) -> Optional[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30) as http:
        games = parse_things(await _get(http, "thing", {"id": bgg_id}))
    return games[0] if games else None


async def download_image(url: Optional[str]) -> Optional[bytes]:
    """Image bytes from BGG's CDN (another host: no Authorization header)."""
    if not url or not url.startswith("https://"):
        return None
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as http:
        img = await http.get(url)
    img.raise_for_status()
    if not img.headers.get("content-type", "").startswith("image/"):
        return None
    if len(img.content) > MAX_IMAGE_BYTES:
        return None
    return img.content


async def find_cover(
    name: str, year: Optional[int]
) -> Optional[tuple[int, Optional[bytes]]]:
    """(BGG id, image bytes or None) for a game found by its exact name, or
    None when BGG has no such game or no token is set."""
    if not settings.bgg_token or not name:
        return None
    async with httpx.AsyncClient(timeout=30) as http:
        game_id = pick_game_id(
            await _get(
                http, "search", {"query": name, "type": "boardgame", "exact": 1}
            ),
            year,
        )
        if game_id is None:
            return None
        url = image_url(await _get(http, "thing", {"id": game_id}))
    return game_id, await download_image(url)
