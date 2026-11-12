from functools import lru_cache
from pathlib import Path

from google import genai
from pydantic_settings import BaseSettings

# rule_chunks.embedding is vector(768) in deploy/schema.sql; changing this
# needs a schema change and a re-embed of every game.
EMBED_DIM = 768


class AISettings(BaseSettings):
    """Env-driven. GOOGLE_API_KEY is read by google-genai and ADK directly.

    Gemini model IDs get retired often; override them by env var rather than
    code when one is shut down."""

    chat_model: str = "gemini-3.5-flash"
    extract_model: str = "gemini-3.5-flash"
    embed_model: str = "gemini-embedding-001"
    image_model: str = "gemini-3.1-flash-image"
    # Share of page 1 covered by raster images for it to count as a cover
    # photo; below this a cover is generated instead. Tune if real
    # rulebooks get misclassified.
    cover_min_image_ratio: float = 0.5
    data_dir: Path = Path("/data")
    # Approved BoardGameGeek app token (boardgamegeek.com/applications);
    # empty = no BGG box art.
    bgg_token: str = ""


settings = AISettings()


@lru_cache
def client() -> genai.Client:
    return genai.Client()


def data_path(relative: str) -> Path:
    """Absolute path for a path stored in the DB (relative to data_dir)."""
    return settings.data_dir / relative
