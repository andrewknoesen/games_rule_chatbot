from fastapi import FastAPI

from rules_api.api import api

app: FastAPI = api.app
