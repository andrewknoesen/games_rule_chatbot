#! /bin/bash
set -e

basepath=$(dirname "$0")
cd "$basepath/../"

uv sync
uv lock
docker build -t game_api .
docker run --env-file .env -p 8000:8000 game_api
