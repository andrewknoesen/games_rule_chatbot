#!/usr/bin/env python3

from omymodels import create_models  # type: ignore

ddl = """
CREATE TABLE games (
    id serial PRIMARY KEY,
    name varchar(255) NOT NULL,
    description text,
    game_types text[],
    game_mechanics text[],
    min_players integer NOT NULL,
    max_players integer NOT NULL,
    min_playtime_minutes integer,
    max_playtime_minutes integer,
    min_age integer,
    complexity_rating numeric(3, 2),
    year_published integer,
    publisher varchar(255),
    designer varchar(255),
    minio_rulebook_path varchar(500),
    minio_image_path varchar(500),
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP
);
"""
result = create_models(ddl, models_type="pydantic")["code"]
print(result)
