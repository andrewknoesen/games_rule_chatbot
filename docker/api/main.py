from fastapi import FastAPI
from games_rule_api.api import api

app: FastAPI = api.app
