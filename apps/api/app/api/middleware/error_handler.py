"""
Global error handler middleware.

Catches RazorGrowthError exceptions and returns standardized
API error responses matching the API specification.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import RazorGrowthError

logger = logging.getLogger(__name__)


async def razorgrowth_error_handler(
    request: Request,
    exc: RazorGrowthError,
) -> JSONResponse:
    """Handle RazorGrowthError exceptions with standard error envelope."""

    request_id = getattr(request.state, "request_id", None)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": request_id,
        },
    )


async def unhandled_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions. Never leak stack traces to clients."""

    request_id = getattr(request.state, "request_id", None)

    logger.exception(
        "Unhandled exception [request_id=%s]: %s",
        request_id,
        str(exc),
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "details": {},
            },
            "request_id": request_id,
        },
    )
