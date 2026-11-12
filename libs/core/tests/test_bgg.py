from games_rule_core.ai.bgg import image_url, pick_game_id

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
