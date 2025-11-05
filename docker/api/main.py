from fastapi import FastAPI
from rules_api.api import api  # type: ignore

app: FastAPI = api.app
