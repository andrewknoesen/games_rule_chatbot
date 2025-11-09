import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel


class Game(SQLModel, table=True):
    __tablename__: str = "game_rules"  # type: ignore

    id: int = Field(default=None, primary_key=True)
    name: str
    description: Optional[str]
    game_types: Optional[List[str]]
    game_mechanics: Optional[List[str]]
    min_players: int
    max_players: int
    min_playtime_minutes: Optional[int]
    max_playtime_minutes: Optional[int]
    min_age: Optional[int]
    complexity_rating: Optional[float]
    year_published: Optional[int]
    publisher: Optional[str]
    designer: Optional[str]
    minio_rulebook_path: Optional[str]
    minio_image_path: Optional[str]
    created_at: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.now
    )
    updated_at: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.now
    )

    class Config:
        extra: str = "forbid"


class Rulebook(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    game_id: int
    document_type: str
    minio_bucket: str
    minio_object_path: str
    file_name: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    uploaded_at: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.now
    )

    class Config:
        extra: str = "forbid"


class GameWithRulebooks(Game):
    rulebooks: List[Rulebook] = []
