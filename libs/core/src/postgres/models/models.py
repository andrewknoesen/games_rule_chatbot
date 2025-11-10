from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, String, func
from sqlmodel import Column, Field, Relationship, SQLModel


# Base model with shared fields (no table=True)
class GameBase(SQLModel):
    name: str
    description: Optional[str] = None
    game_types: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )
    game_mechanics: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )
    min_players: int
    max_players: int
    min_playtime_minutes: Optional[int] = None
    max_playtime_minutes: Optional[int] = None
    min_age: Optional[int] = None
    complexity_rating: Optional[float] = None
    year_published: Optional[int] = None
    publisher: Optional[str] = None
    designer: Optional[str] = None
    minio_rulebook_path: Optional[str] = None
    minio_image_path: Optional[str] = None


# Database table model (adds ID and timestamps)
class Game(GameBase, table=True):
    __tablename__: str = "games"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": func.now()}
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )

    rulebooks: List["Rulebook"] = Relationship(back_populates="game")


class RulebookBase(SQLModel):
    game_id: int = Field(foreign_key="games.id")
    document_type: str
    minio_bucket: str
    minio_object_path: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None


class Rulebook(RulebookBase, table=True):
    __tablename__: str = "game_documents"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    uploaded_at: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": func.now()}
    )

    game: Optional["Game"] = Relationship(back_populates="rulebooks")
