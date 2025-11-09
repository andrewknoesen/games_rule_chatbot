from fastapi import APIRouter

from rules_api.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health/ready")
@router.get("/health/live")
@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple health check endpoint"""
    return HealthResponse(status="ok", message="Service is healthy")


# @router.get("/health/live")
# async def liveness():
#     # Simple check - is the process running?
#     return {"status": "alive"}


# @router.get("/health/ready")
# async def readiness():
#     # Check if dependencies are available
#     try:
#         # Check PostgreSQL
#         await db.execute("SELECT 1")
#         # Check Weaviate
#         await weaviate_client.is_ready()
#         # Check MinIO
#         await minio_client.bucket_exists("game-rules")
#         return {"status": "ready"}
#     except Exception:
#         raise HTTPException(status_code=503, detail="Not ready")
