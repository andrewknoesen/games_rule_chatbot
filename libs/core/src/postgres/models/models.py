import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, String
from sqlmodel import Column, Field, Relationship, SQLModel


class Game(SQLModel, table=True):
    __tablename__: str = "games"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
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
    created_at: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.now
    )
    updated_at: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.now
    )

    rulebooks: List["Rulebook"] = Relationship(back_populates="game")


class Rulebook(SQLModel, table=True):
    __tablename__: str = "game_documents"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    document_type: str
    minio_bucket: str
    minio_object_path: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.now
    )

    game: Optional["Game"] = Relationship(back_populates="rulebooks")
