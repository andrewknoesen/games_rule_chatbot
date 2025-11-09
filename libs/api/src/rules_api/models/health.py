from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Simple health check response"""

    status: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {"status": "ok", "message": "Service is healthy"}
        }
