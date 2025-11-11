from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from games_rule_api.exceptions.exceptions import integrity_error_handler
from games_rule_api.routers import games, health, settings

app = FastAPI()
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.include_router(games.router)
app.include_router(settings.router)
app.include_router(health.router)
