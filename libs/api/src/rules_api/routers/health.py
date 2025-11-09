from fastapi import APIRouter

from rules_api.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple health check endpoint"""
    return HealthResponse(status="ok", message="Service is healthy")
