from games_rule_core.ai.bgg import image_url, parse_things, pick_game_id, rank_search

SEARCH = """<?xml version="1.0" encoding="utf-8"?>
<items total="2" termsofuse="https://boardgamegeek.com/xmlapi/termsofuse">
  <item type="boardgame" id="111"><name type="primary" value="Catan"/>
    <yearpublished value="1995"/></item>
  <item type="boardgame" id="222"><name type="primary" value="Catan"/>
    <yearpublished value="2015"/></item>
</items>"""

THING = """<?xml version="1.0" encoding="utf-8"?>
<items termsofuse="https://boardgamegeek.com/xmlapi/termsofuse">
  <item type="boardgame" id="222">
    <thumbnail>https://cf.geekdo-images.com/t.jpg</thumbnail>
    <image> https://cf.geekdo-images.com/full.jpg </image>
  </item>
</items>"""


def test_pick_game_id() -> None:
    assert pick_game_id(SEARCH, 2015) == 222  # year breaks the tie
    assert pick_game_id(SEARCH, 1999) == 111  # no year match: first hit
    assert pick_game_id(SEARCH, None) == 111
    assert pick_game_id('<items total="0"/>', 2015) is None


def test_image_url() -> None:
    assert image_url(THING) == "https://cf.geekdo-images.com/full.jpg"
    assert image_url("<items><item id='1'/></items>") is None


SEARCH_MANY = """<items total="3">
  <item type="boardgame" id="3"><name type="alternate" value="Catan: Junior"/></item>
  <item type="boardgame" id="1"><name type="primary" value="My Catan Clone"/></item>
  <item type="boardgame" id="2"><name type="primary" value="CATAN"/></item>
  <item type="boardgame" id="2"><name type="alternate" value="Die Siedler"/></item>
</items>"""


def test_rank_search_puts_exact_then_prefix_first() -> None:
    assert rank_search(SEARCH_MANY, "catan", 20) == [2, 3, 1]
    assert rank_search(SEARCH_MANY, "catan", 1) == [2]


def test_parse_things() -> None:
    xml = """<items><item type="boardgame" id="13">
      <thumbnail>https://cf.geekdo-images.com/t.jpg</thumbnail>
      <name type="alternate" value="Settlers"/><name type="primary" value="CATAN"/>
      <yearpublished value="1995"/>
      <link type="boardgamecategory" id="1" value="Negotiation"/>
      <link type="boardgamepublisher" id="2" value="KOSMOS"/>
      <statistics><ratings><usersrated value="120000"/></ratings></statistics>
    </item></items>"""
    [game] = parse_things(xml)
    assert game["name"] == "CATAN" and game["year"] == 1995
    assert game["publishers"] == ["KOSMOS"] and game["users_rated"] == 120000
    assert game["thumbnail"] == "https://cf.geekdo-images.com/t.jpg"
    assert game["image"] is None
