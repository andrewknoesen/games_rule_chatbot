"""Box art from BoardGameGeek's XML API2.

Needs an approved BGG application token in BGG_TOKEN; without one this is a
no-op and ingestion falls back to the rulebook or a generated cover. Terms
(https://boardgamegeek.com/using_the_xml_api): non-commercial use, credit
BGG, call from the server and cache, and do not modify the data, so the image
is stored exactly as downloaded."""

from typing import Optional
from xml.etree import ElementTree  # nosec B405 (see _parse)

import httpx

from games_rule_core.ai.config import settings

API = "https://boardgamegeek.com/xmlapi2"  # no www: tokens fail there
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _parse(xml: str) -> ElementTree.Element:
    # BGG's own responses; the bundled expat (>= 2.4) refuses entity-expansion
    # bombs, so stdlib parsing is enough here.
    return ElementTree.fromstring(xml)  # nosec B314


def pick_game_id(search_xml: str, year: Optional[int]) -> Optional[int]:
    """Id from an exact-name search; prefer the rulebook's publication year
    when several games share the name (reprints, remakes)."""
    ids: list[int] = []
    for item in _parse(search_xml).iter("item"):
        game_id = int(item.get("id", "0"))
        found_year = item.find("yearpublished")
        if year is not None and found_year is not None:
            if found_year.get("value") == str(year):
                return game_id
        ids.append(game_id)
    # ponytail: same name, no year match -> first hit; add a manual override
    # if wrong covers show up.
    return ids[0] if ids else None


def image_url(thing_xml: str) -> Optional[str]:
    node = _parse(thing_xml).find("item/image")
    url = (node.text or "").strip() if node is not None else ""
    return url if url.startswith("https://") else None


async def find_cover(
    name: str, year: Optional[int]
) -> Optional[tuple[int, Optional[bytes]]]:
    """(BGG id, image bytes or None), or None when BGG has no such game or
    no token is set."""
    if not settings.bgg_token or not name:
        return None
    auth = {"Authorization": f"Bearer {settings.bgg_token}"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as http:
        resp = await http.get(
            f"{API}/search",
            params={"query": name, "type": "boardgame", "exact": 1},
            headers=auth,
        )
        resp.raise_for_status()
        game_id = pick_game_id(resp.text, year)
        if game_id is None:
            return None
        resp = await http.get(f"{API}/thing", params={"id": game_id}, headers=auth)
        resp.raise_for_status()
        url = image_url(resp.text)
        if url is None:
            return game_id, None
        # Image CDN is another host: no Authorization header there.
        img = await http.get(url)
        img.raise_for_status()
        if not img.headers.get("content-type", "").startswith("image/"):
            return game_id, None
        if len(img.content) > MAX_IMAGE_BYTES:
            return game_id, None
        return game_id, img.content
