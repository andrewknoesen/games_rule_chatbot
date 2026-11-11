# Built from the repo root (context "."), straight from the uv workspace, so
# one PR ships a change to core + api + image together.
#   docker build -f docker/api/Dockerfile .

# Build stage
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/python UV_PYTHON_PREFERENCE=only-managed

RUN uv python install 3.13

WORKDIR /app

# Third-party deps first (cached until uv.lock changes).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=libs,target=libs \
    uv sync --frozen --no-dev --no-editable --package games_rule_api --no-install-workspace

# Then the workspace packages themselves.
COPY pyproject.toml uv.lock ./
COPY libs ./libs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package games_rule_api

RUN find /app/.venv -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

# Runtime stage - minimal distroless image
FROM gcr.io/distroless/cc-debian12

WORKDIR /app

COPY --from=builder /python /python
COPY --from=builder /app/.venv /app/.venv
COPY docker/api/main.py /app/main.py

ENV PATH="/python/bin:/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1

CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0"]
