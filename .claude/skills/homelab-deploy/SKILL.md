---
name: homelab-deploy
description: Deploy, update, roll back, or inspect the games rule chatbot (Postgres + FastAPI) on the homelab host via Docker Compose. Use for "deploy to homelab", "is the API up", "roll back the api", "show api logs", "open psql", or first-time setup on 192.168.0.200.
---

# Homelab deploy

The app runs on the homelab host (`ssh homelab`, 192.168.0.200, Debian 12,
4 CPU / 7.7 GB RAM) as the Compose project in [deploy/compose.yaml](../../../deploy/compose.yaml):
`postgres` (postgres:17-alpine) and `api` (`ghcr.io/andrewknoesen/api_image`).

**No Kubernetes on that host.** A k3s cluster running this app starved the
box and was removed on 2026-08-29. Do not reintroduce Helm/k3s/Argo CD there.
`charts/` in this repo is the dead k8s deployment.

- Host checkout: `~/Documents/Projects/games_rule_chatbot` (https clone of the public repo)
- Secrets: `deploy/.env` on the host only (`POSTGRES_PASSWORD`, optional `API_TAG`)
- API: `http://192.168.0.200:8720` (LAN/tailnet only; the API has no auth, so do not route it publicly)
- Memory caps: 256m per container. Host RAM is tight (check `free -h` before adding anything).

## How updates reach the host

GitHub's cloud runners cannot reach the LAN, so the host pulls. A crontab line
on the host runs every 15 min:

```
*/15 * * * * cd ~/Documents/Projects/games_rule_chatbot && git pull -q --ff-only && docker compose -f deploy/compose.yaml up -d --pull always --quiet-pull >> ~/logs/games_rule_chatbot_deploy.log 2>&1
```

`up -d --pull always` recreates a container only when its image or config
changed, so the idle runs do nothing. Merging to `main` → `deploy.yaml`
builds and pushes the image (only when `docker/api/pyproject.toml` version is new) →
`latest` moves → cron picks it up within 15 min.

## Tasks

Run everything through `ssh homelab '<cmd>'`, from `~/Documents/Projects/games_rule_chatbot` on the host.

**Deploy now (skip the cron wait)**
```bash
ssh homelab 'cd ~/Documents/Projects/games_rule_chatbot && git pull --ff-only && docker compose -f deploy/compose.yaml up -d --pull always'
```

**Status / health**
```bash
ssh homelab 'cd ~/Documents/Projects/games_rule_chatbot && docker compose -f deploy/compose.yaml ps && curl -fsS localhost:8720/health && docker stats --no-stream games_rule_chatbot-api-1 games_rule_chatbot-postgres-1'
```

**Logs**: `docker compose -f deploy/compose.yaml logs --tail 100 api` (or `postgres`).

**psql**: `docker compose -f deploy/compose.yaml exec postgres psql -U gamesuser -d games`.
Query examples: [docs/db_query_ref.md](../../../docs/db_query_ref.md).

**Roll back the API**: set `API_TAG=<version>` in the host's `deploy/.env`
(tags list: `curl -s` the GHCR tags API or check GitHub releases `api_image-*`),
then `up -d`. Remove the line to return to `latest`.

**Backup the DB** (do this before any schema change or Postgres major bump):
```bash
ssh homelab 'mkdir -p ~/backups && cd ~/Documents/Projects/games_rule_chatbot && docker compose -f deploy/compose.yaml exec -T postgres pg_dump -U gamesuser games | gzip > ~/backups/games_rule_chatbot-$(date +%F).sql.gz'
```

## Schema changes

[deploy/schema.sql](../../../deploy/schema.sql) runs only when the `pgdata` volume is empty.
For an existing DB, take a backup, then apply the change by hand with `psql`
and also edit `schema.sql` so fresh installs match. Keep it in sync with the
SQLModel tables in `libs/core/src/games_rule_core/postgres/models/models.py`
(`games`, `game_documents`).

## First-time setup (one off)

1. `git clone https://github.com/andrewknoesen/games_rule_chatbot.git ~/Documents/Projects/games_rule_chatbot`
2. Write `deploy/.env` from `deploy/.env.example` with a random password (`openssl rand -hex 24`). Do not print it.
3. `docker compose -f deploy/compose.yaml up -d`, then check health as above.
4. `mkdir -p ~/logs` and add the crontab line above (`crontab -l` first, keep existing lines).
5. Update the homelab repo (`~/Documents/Projects/homelab` on the Mac): add a row to
   ARCHITECTURE.md "Projects & Services" plus the mermaid diagram, per that repo's CLAUDE.md.

## Homelab rules (from the homelab repo)

- Back up a config to `~/backups/` on the host before editing it.
- Never delete the `pgdata` volume or user data yourself. Hand the exact command to Andrew.
- Port 8000 is taken on the host; 8720 is this app's.
