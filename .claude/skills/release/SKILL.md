---
name: release
description: Ship a change to games_rule_core, games_rule_api, the api_image or the games_ui image — version bumps, RELEASE.md notes and pins in one PR. Use for "release", "bump version", "publish", "ship this change", or when a change needs to reach the homelab.
---

# Release

`.github/workflows/deploy.yaml` runs on every push to `main`. Each job builds
**only if** its `<name>-<version>` git tag does not exist yet, so an unbumped
version skips silently and the change never ships.

| What changed | Bump | Ships as |
|---|---|---|
| `libs/core` | `libs/core/pyproject.toml` + `libs/core/RELEASE.md` | wheel on the gh-pages index |
| `libs/api` | `libs/api/pyproject.toml` + `libs/api/RELEASE.md` | wheel on the gh-pages index |
| anything the API runs (`libs/*`, `docker/api/`) | `docker/api/pyproject.toml` `version` | `ghcr.io/andrewknoesen/api_image:<ver>` + `latest` |
| `frontend/` | `frontend/package.json` `version` (also `package-lock.json`, via `npm version <ver> --no-git-tag-version`) | `ghcr.io/andrewknoesen/games_ui:<ver>` + `latest` |

The API image builds straight from the uv workspace source (`docker/api/Dockerfile`,
context `.`). It does **not** wait for the wheels, so one PR ships everything.
The wheels still publish for anything that installs them.

## Steps

1. Work out what changed: `git diff main --stat -- libs/ docker/ frontend/`.
2. Bump each affected version (semver: patch for fixes, minor for features).
   - For a lib, add a `## <ver>` section with one-line bullets at the top of its `RELEASE.md`.
   - If core was bumped, update the api's pin: `games-rule-core==<new core ver>` in `libs/api/pyproject.toml`.
   - Any `libs/*` change that should reach the homelab also needs the `docker/api` bump.
3. Run `uv lock`.
4. Run the checks (the same ones as `ci.yaml`):
   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run mypy --strict --config-file pyproject.toml libs && uv run pytest libs/core/tests -q --no-cov && bash .hooks/validate_release_notes.sh
   ```
   If you touched the UI, also run `cd frontend && npm run build`.
5. Commit on a branch, push and open a PR. `main` is protected by the `no-commit-to-branch` hook.
6. After merge, watch the run with `gh run watch`. The homelab cron pulls `latest` within 15 min. To deploy at once or to verify, use the `homelab-deploy` skill.

## Gotchas

- Keep `.python-version` on a Python that pydantic-core and PyMuPDF ship wheels for (3.13 now). The Dockerfile installs 3.13 itself; keep the two aligned. Renovate's `pyenv` manager is disabled for this reason.
- A version number can never be reused. Once a tag exists, fix forward with a new patch version.
- A schema change (`deploy/schema.sql`) is not applied by a deploy. See "Schema changes" in the `homelab-deploy` skill.
- On macOS, if `import games_rule_core` fails after `uv sync`, the `.pth` files got the hidden flag (Python 3.13 skips them). Fix it with `chflags nohidden .venv/lib/python3.13/site-packages/*.pth`.
