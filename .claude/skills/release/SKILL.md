---
name: release
description: Cut a release of games_rule_core, games_rule_api, and/or the api_image Docker image — version bumps, RELEASE.md notes, dependency pins, lockfiles, and the two-PR order the pipeline needs. Use for "release", "bump version", "publish the package", "ship this change", or when a libs/ change needs to reach the homelab.
---

# Release

Three artifacts, published in a chain by `.github/workflows/deploy.yaml` on push to `main`:

```
libs/core  (games_rule_core)  ──pinned by──▶  libs/api  (games_rule_api)  ──pinned by──▶  docker/api  (api_image)
   wheel → gh-pages PyPI index                    wheel → gh-pages index                     image → ghcr.io/andrewknoesen/api_image
```

Each job builds **only if** the `<name>-<version>` git tag does not exist yet.
An unbumped version means the job skips silently. Code merged without a bump never ships.

## Rules the pipeline enforces

- `libs/<pkg>/RELEASE.md` must have a non-empty `## <version>` section matching
  `pyproject.toml`. Check locally with `bash .hooks/validate_release_notes.sh`.
- `docker/api/uv.lock` resolves `games_rule_api` from the **published** index
  (`https://andrewknoesen.github.io/games_rule_chatbot/simple/`). It cannot lock a
  wheel that is not published yet.
- `main` is protected by the `no-commit-to-branch` pre-commit hook: work on a branch and open a PR.

## Steps

Ask which packages changed if unclear (`git diff main --stat -- libs/ docker/`).
Use semver: patch for fixes, minor for features. The existing notes are one-line bullets.

### PR 1: libraries (skip parts that did not change)

1. **core changed**: bump `version` in `libs/core/pyproject.toml`, and add `## <ver>` with bullets at the top of `libs/core/RELEASE.md`.
2. **api changed, or core bumped**: bump `libs/api/pyproject.toml` `version`. If core was bumped, update its pin `games-rule-core==<new core ver>`. Add a `libs/api/RELEASE.md` section.
3. `uv lock` at the repo root, then `uv sync --all-packages`.
4. Run checks: `uv run ruff check . && uv run ruff format --check . && uv run mypy --strict --config-file pyproject.toml libs && bash .hooks/validate_release_notes.sh`.
5. Commit, push, open the PR. After merge, wait for the `deploy.yaml` run to publish the wheels (`gh run watch`).

### PR 2: image (needs PR 1's wheels on the index)

1. Check that the wheel is live: `curl -s https://andrewknoesen.github.io/games_rule_chatbot/simple/games-rule-api/ | grep <new api ver>`. gh-pages can lag a minute.
2. In `docker/api/pyproject.toml`, set the pin to `games_rule_api==<new api ver>` and bump `version`.
3. `cd docker/api && uv lock --refresh`.
4. Commit, push, open the PR, merge. `deploy.yaml` then pushes `api_image:<ver>` and `latest`.
5. The homelab cron pulls `latest` within 15 min. To deploy at once or verify, use the `homelab-deploy` skill.

If only `docker/api` changed (Dockerfile, `main.py`), do PR 2 alone.

## Gotchas

- Keep `.python-version` on a version that pydantic-core ships wheels for (3.13 now). Renovate bumped it to 3.15 once and broke `uv sync`.
- The Dockerfile installs Python 3.13 on its own. Keep both versions aligned.
- A version number can never be reused. Once a tag exists, fix forward with a new patch version.
