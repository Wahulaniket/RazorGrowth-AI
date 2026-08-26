"""
Request ID middleware.

Generates or propagates a unique request ID for every request,
enabling end-to-end request tracing across the system.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every request has a unique request ID.

    If the client sends an X-Request-ID header, it is preserved.
    Otherwise, a new UUID is generated.

    The request ID is:
    - Stored in request.state.request_id for use by handlers
    - Returned in the X-Request-ID response header
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
