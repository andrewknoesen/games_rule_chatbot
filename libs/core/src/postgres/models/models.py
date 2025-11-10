from datetime import datetime
from typing import List, Optional

from pydantic import field_validator, model_validator
from sqlalchemy import ARRAY, String, func
from sqlmodel import Column, Field, Relationship, SQLModel
from typing_extensions import Self


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

    @field_validator("min_players", "max_players")
    @classmethod
    def players_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Player count must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_player_ranges(self) -> Self:
        """Validate that max_players >= min_players"""
        if self.max_players < self.min_players:
            raise ValueError(
                f"max_players ({self.max_players}) must be greater than or equal to "
                f"min_players ({self.min_players})"
            )
        return self

    @model_validator(mode="after")
    def validate_playtime_ranges(self) -> Self:
        """Validate that max_playtime >= min_playtime if both are set"""
        if (
            self.min_playtime_minutes is not None
            and self.max_playtime_minutes is not None
            and self.max_playtime_minutes < self.min_playtime_minutes
        ):
            raise ValueError(
                f"max_playtime_minutes ({self.max_playtime_minutes}) must be greater than or equal to "
                f"min_playtime_minutes ({self.min_playtime_minutes})"
            )
        return self

    @field_validator("complexity_rating")
    @classmethod
    def complexity_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (1.0 <= v <= 5.0):
            raise ValueError("complexity_rating must be between 1.0 and 5.0")
        return v

    @field_validator("min_age", "min_playtime_minutes", "max_playtime_minutes")
    @classmethod
    def positive_if_set(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Value must be greater than 0 if provided")
        return v


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
