-- Runs once, when the pgdata volume is empty. For an existing DB, apply
-- changes by hand (see .claude/skills/homelab-deploy) and mirror them here.
-- Keep in sync with libs/core/src/games_rule_core/postgres/models/models.py.

CREATE EXTENSION IF NOT EXISTS vector;

-- One row per uploaded rulebook. Everything except id/name/status is filled
-- in by ingestion (Gemini extraction), so most columns are nullable.
CREATE TABLE IF NOT EXISTS games (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'processing'
    CHECK (status IN ('processing', 'ready', 'failed')),
  error TEXT,
  description TEXT,
  objective TEXT,
  game_types TEXT[],
  game_mechanics TEXT[],
  min_players INTEGER CHECK (min_players > 0),
  max_players INTEGER CHECK (max_players >= min_players),
  min_playtime_minutes INTEGER CHECK (min_playtime_minutes > 0),
  max_playtime_minutes INTEGER CHECK (max_playtime_minutes >= min_playtime_minutes),
  min_age INTEGER CHECK (min_age > 0),
  complexity_rating DECIMAL(3,2) CHECK (complexity_rating BETWEEN 1.00 AND 5.00),
  year_published INTEGER,
  publisher VARCHAR(255),
  designer VARCHAR(255),
  cover_path VARCHAR(500),
  -- Structured rules, shaped for the frontend's detail page.
  components JSONB,
  setup JSONB,
  turn_structure JSONB,
  rules JSONB,
  win_conditions JSONB,
  special_rules JSONB,
  glossary JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files stored for a game (the rulebook PDF today). Paths are relative to
-- the API's DATA_DIR volume.
CREATE TABLE IF NOT EXISTS game_documents (
  id SERIAL PRIMARY KEY,
  game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  document_type VARCHAR(50) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_size_bytes BIGINT,
  mime_type VARCHAR(100),
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (game_id, file_path)
);

-- Rulebook text chunks for RAG. 768 = the embedding output_dimensionality
-- set in games_rule_core.ai.config.
CREATE TABLE IF NOT EXISTS rule_chunks (
  id SERIAL PRIMARY KEY,
  game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  page INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding vector(768) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_games_name ON games(name);
CREATE INDEX IF NOT EXISTS idx_games_types ON games USING GIN(game_types);
CREATE INDEX IF NOT EXISTS idx_games_mechanics ON games USING GIN(game_mechanics);
CREATE INDEX IF NOT EXISTS idx_game_documents_game_id ON game_documents(game_id);
CREATE INDEX IF NOT EXISTS idx_rule_chunks_game_id ON rule_chunks(game_id);
CREATE INDEX IF NOT EXISTS idx_rule_chunks_embedding
  ON rule_chunks USING hnsw (embedding vector_cosine_ops);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER update_games_updated_at BEFORE UPDATE ON games
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
