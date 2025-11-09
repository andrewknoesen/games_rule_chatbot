from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from fastapi import FastAPI

env_path: Path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
print(dotenv_values())
from rules_api.api import api  # noqa: E402

app: FastAPI = api.app
