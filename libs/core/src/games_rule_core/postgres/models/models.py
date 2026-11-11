"""Table models. Keep in sync with deploy/schema.sql (the DB is created from
that file, not from these models). rule_chunks has no model: it is only
touched through raw SQL in games_rule_core.ai.rag (pgvector column)."""

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import ARRAY, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

JsonList = Optional[List[dict[str, Any]]]


def _jsonb() -> Any:
    return Field(default=None, sa_column=Column(JSONB))


class Game(SQLModel, table=True):
    __tablename__: str = "games"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    status: str = "processing"  # processing | ready | failed
    error: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    game_types: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )
    game_mechanics: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    min_playtime_minutes: Optional[int] = None
    max_playtime_minutes: Optional[int] = None
    min_age: Optional[int] = None
    complexity_rating: Optional[float] = None
    year_published: Optional[int] = None
    publisher: Optional[str] = None
    designer: Optional[str] = None
    cover_path: Optional[str] = None

    components: JsonList = _jsonb()
    setup: JsonList = _jsonb()
    turn_structure: JsonList = _jsonb()
    rules: JsonList = _jsonb()
    win_conditions: JsonList = _jsonb()
    special_rules: JsonList = _jsonb()
    glossary: JsonList = _jsonb()

    created_at: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": func.now()}
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )


class GameDocument(SQLModel, table=True):
    __tablename__: str = "game_documents"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id", ondelete="CASCADE")
    document_type: str
    file_path: str  # relative to DATA_DIR
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": func.now()}
    )
