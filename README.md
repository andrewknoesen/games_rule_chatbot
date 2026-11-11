## Games Rule Chatbot

Upload a board game's rulebook PDF and the game is added to your library:

- Gemini reads the rulebook and extracts players, playtime, components, setup, turn structure, rules and a glossary.
- The pages are embedded into pgvector so a rules judge can answer questions about them.
- The judge is a Google ADK agent that cites page numbers.
- A thumbnail comes from the rulebook's cover page. If page 1 isn't a cover photo, Gemini generates one.

### Layout

```
libs/core      games_rule_core: DB models/session, ai/ (ingestion, RAG, ADK agent)
libs/api       games_rule_api: FastAPI routes (upload, games, cover, ask)
docker/api     API image (built from the uv workspace) + its version
frontend/      React UI (Vite), served by nginx, proxies /api
deploy/        Homelab Docker Compose stack + Postgres schema
.claude/skills homelab-deploy and release workflows for Claude Code
```

### Development

```bash
uv sync
uv run pytest libs/core/tests -q --no-cov
cd frontend && npm ci && npm run dev   # proxies /api to localhost:8000
```

Checks run in CI on every PR (`.github/workflows/ci.yaml`): ruff, mypy `--strict`, tests, release notes, compose config, and the frontend build. Install the hooks with `uv run pre-commit install`.

### Releases and deployment

- Bump a version and merge to `main`. `deploy.yaml` then publishes the wheels to the gh-pages index and the images to GHCR. The `release` skill has the details.
- The app runs on the homelab host as the Compose stack in `deploy/`. A cron job on the host pulls new images every 15 minutes. The `homelab-deploy` skill has the details.

`charts/` is the old Kubernetes deployment and is no longer used.
