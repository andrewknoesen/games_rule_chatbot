# Inserting data with arrays
```sql
INSERT INTO games (name, description, game_types, game_mechanics, min_players, max_players)
VALUES (
  'Catan',
  'A game about settling an island',
  ARRAY['Strategy', 'Family'],
  ARRAY['Dice Rolling', 'Resource Management', 'Trading'],
  3,
  4
);
```
# Searching for games with specific types
```sql
-- Find all strategy games
SELECT * FROM games WHERE 'Strategy' = ANY(game_types);

-- Find games that contain both Strategy AND Family
SELECT * FROM games WHERE game_types @> ARRAY['Strategy', 'Family'];

-- Find games with any of these mechanics
SELECT * FROM games WHERE game_mechanics && ARRAY['Dice Rolling', 'Card Drafting'];
```
# Updating arrays
```sql
-- Replace entire array
UPDATE games SET game_types = ARRAY['Strategy', 'Economic'] WHERE id = 1;

-- Append to array
UPDATE games SET game_mechanics = array_append(game_mechanics, 'Auction/Bidding') WHERE id = 1;

-- Remove from array
UPDATE games SET game_mechanics = array_remove(game_mechanics, 'Dice Rolling') WHERE id = 1;
```