from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from rules_api.exceptions.exceptions import integrity_error_handler
from rules_api.routers import games, health, settings

app = FastAPI()
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.include_router(games.router)
app.include_router(settings.router)
app.include_router(health.router)
