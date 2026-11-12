---
name: homelab-deploy
description: Deploy, update, roll back, or inspect the games rule chatbot (Postgres/pgvector + FastAPI/ADK + React UI) on the homelab host via Docker Compose. Use for "deploy to homelab", "is the API up", "why did a rulebook fail", "roll back the api", "show api logs", "open psql", or first-time setup on 192.168.0.200.
---

# Homelab deploy

The app runs on the homelab host (`ssh homelab`, 192.168.0.200, Debian 12,
4 CPU / 7.7 GB RAM) as the Compose project in [deploy/compose.yaml](../../../deploy/compose.yaml):
- `postgres`: `pgvector/pgvector:pg17`. Holds the games, documents and `rule_chunks` vectors.
- `api`: `ghcr.io/andrewknoesen/api_image`. FastAPI plus the ingestion pipeline and the ADK rules judge, calling Gemini.
- `ui`: `ghcr.io/andrewknoesen/games_ui`. nginx serves the React app and proxies `/api` to `api`.

**No Kubernetes on that host.** A k3s cluster running this app starved the
box and was removed on 2026-08-29. Do not reintroduce Helm/k3s/Argo CD there.
`charts/` in this repo is the dead k8s deployment.

- Host checkout: `~/Documents/Projects/games_rule_chatbot` (https clone of the public repo)
- Secrets: `deploy/.env` on the host only. It holds `POSTGRES_PASSWORD`, `GOOGLE_API_KEY`, and optionally `API_TAG`, `UI_TAG` and model overrides such as `CHAT_MODEL`.
- UI: `http://192.168.0.200:8721`. API: `http://192.168.0.200:8720`. Both are LAN/tailnet only, with no auth. Every upload and question costs Gemini money, so never route them publicly.
- Files: the `games_rule_chatbot_files` volume, mounted at `/data`, holds `games/<id>/rulebook.pdf` and `cover.png`.
- Memory caps: api 768m, postgres 384m, ui 64m. Host RAM is tight, so check `free -h` before raising them.

## How updates reach the host

GitHub's cloud runners cannot reach the LAN, so the host pulls. A crontab line
on the host runs every 15 min:

```
*/15 * * * * cd ~/Documents/Projects/games_rule_chatbot && git pull -q --ff-only && flock -n /tmp/games_rule_chatbot-deploy.lock docker compose -f deploy/compose.yaml up -d --pull always --quiet-pull >> ~/logs/games_rule_chatbot_deploy.log 2>&1
```

`up -d --pull always` recreates a container only when its image or config
changed, so the idle runs do nothing. Both the cron line and a manual deploy take the same `flock`. Without it, the two once raced to recreate the api container and left a `Conflict. The container name ... is already in use` error. Merging to `main` → `deploy.yaml`
builds and pushes the images (only when `docker/api/pyproject.toml` or `frontend/package.json` version is new) →
`latest` moves → cron picks it up within 15 min.

## Tasks

Run everything through `ssh homelab '<cmd>'`, from `~/Documents/Projects/games_rule_chatbot` on the host.

**Deploy now (skip the cron wait)**
```bash
ssh homelab 'cd ~/Documents/Projects/games_rule_chatbot && git pull --ff-only && flock /tmp/games_rule_chatbot-deploy.lock docker compose -f deploy/compose.yaml up -d --pull always'
```

**Status / health**
```bash
ssh homelab 'cd ~/Documents/Projects/games_rule_chatbot && docker compose -f deploy/compose.yaml ps && curl -fsS localhost:8720/health && docker stats --no-stream games_rule_chatbot-api-1 games_rule_chatbot-postgres-1 games_rule_chatbot-ui-1'
```

**Why did a rulebook fail?** Run `curl -s localhost:8720/games/<id>`; its `status` and `error` fields say why. For the stack trace, run `docker compose -f deploy/compose.yaml logs api | grep -A20 "ingestion failed for game <id>"`.
A Gemini `404`/`NOT_FOUND` for a model means the model was retired. Set `CHAT_MODEL`, `EXTRACT_MODEL`, `EMBED_MODEL` or `IMAGE_MODEL` in `deploy/.env` to a current ID (see ai.google.dev/gemini-api/docs/models), then `up -d`.
Do not change `EMBED_MODEL` once games exist without re-uploading them, because old and new vectors don't mix.

**Logs**: `docker compose -f deploy/compose.yaml logs --tail 100 api` (or `postgres`).

**psql**: `docker compose -f deploy/compose.yaml exec postgres psql -U gamesuser -d games`.
Query examples: [docs/db_query_ref.md](../../../docs/db_query_ref.md).

**Roll back the API**: set `API_TAG=<version>` in the host's `deploy/.env`
(tags list: `curl -s` the GHCR tags API or check GitHub releases `api_image-*`),
then `up -d`. Remove the line to return to `latest`.

**BGG box art**: covers come from BoardGameGeek only when `BGG_TOKEN` is in the host's `deploy/.env`. The user registers a non-commercial app at https://boardgamegeek.com/applications and creates the token there; the user enters it, never Claude. After adding it, run `docker compose -f deploy/compose.yaml up -d api`, then backfill older games with `docker compose -f deploy/compose.yaml exec api python3 -m games_rule_core.ai.ingest`. A `401` in the api logs means the token is missing or revoked; ingestion then falls back to the rulebook or a generated cover.

**Backup** (do this before any schema change or Postgres major bump). Take the DB and the files together:
```bash
ssh homelab 'mkdir -p ~/backups && cd ~/Documents/Projects/games_rule_chatbot && docker compose -f deploy/compose.yaml exec -T postgres pg_dump -U gamesuser games | gzip > ~/backups/games_rule_chatbot-$(date +%F).sql.gz && docker run --rm -v games_rule_chatbot_files:/data:ro alpine tar czf - -C /data . > ~/backups/games_rule_chatbot-files-$(date +%F).tgz'
```

## Schema changes

[deploy/schema.sql](../../../deploy/schema.sql) runs only when the `pgdata` volume is empty.
For an existing DB, take a backup, then apply the change by hand with `psql`
and also edit `schema.sql` so fresh installs match. Keep it in sync with the
SQLModel tables in `libs/core/src/games_rule_core/postgres/models/models.py`
(`games`, `game_documents`). `rule_chunks` has no model; it is used through raw SQL in `games_rule_core/ai/rag.py`.

## First-time setup (one off)

1. `git clone https://github.com/andrewknoesen/games_rule_chatbot.git ~/Documents/Projects/games_rule_chatbot`
2. Write `deploy/.env` from `deploy/.env.example`, with a random password (`openssl rand -hex 24`) and the user's Gemini key. Do not print either.
3. `docker compose -f deploy/compose.yaml up -d`, then check health as above.
4. `mkdir -p ~/logs` and add the crontab line above (`crontab -l` first, keep existing lines).
5. Update the homelab repo (`~/Documents/Projects/homelab` on the Mac): add a row to
   ARCHITECTURE.md "Projects & Services" plus the mermaid diagram, per that repo's CLAUDE.md.

## Homelab rules (from the homelab repo)

- Back up a config to `~/backups/` on the host before editing it.
- Never delete the `pgdata` volume or user data yourself. Hand the exact command to Andrew.
- Port 8000 is taken on the host; 8720 (API) and 8721 (UI) are this app's.
