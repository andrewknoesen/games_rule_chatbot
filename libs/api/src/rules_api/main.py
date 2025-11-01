from fastapi import FastAPI

from rules_api.routers import games, settings

app = FastAPI()
app.include_router(games.router)
app.include_router(settings.router)
