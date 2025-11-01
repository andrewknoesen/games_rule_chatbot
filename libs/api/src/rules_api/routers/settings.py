from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends

from rules_api.config import Settings

router = APIRouter()


@lru_cache
def get_settings() -> Settings:
    return Settings()


@router.get("/info")
async def info(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    return settings.model_dump()
