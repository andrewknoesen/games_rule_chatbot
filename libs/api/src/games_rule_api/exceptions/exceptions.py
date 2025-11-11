from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


async def integrity_error_handler(
    request: Request,
    exc: Exception,
) -> Response:
    """Convert database integrity errors to proper HTTP responses"""
    # Type guard - ensure it's actually an IntegrityError
    if not isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    error_msg: str = str(exc.orig) if hasattr(exc, "orig") else str(exc)

    if "check constraint" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": "Validation error: Values must meet database constraints. Check that min_players > 0, complexity_rating is 1.0-5.0, etc.",
                "msg": error_msg,
            },
        )
    elif "unique constraint" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Resource already exists",
                "msg": error_msg,
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid data provided",
                "msg": error_msg,
            },
        )
