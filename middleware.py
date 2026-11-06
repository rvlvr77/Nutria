"""Middleware de request-id y latencia (observabilidad básica)."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

logger = logging.getLogger("nutriai.http")

REQUEST_ID_HEADER = "X-Request-ID"


async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming if 0 < len(incoming) <= 64 else uuid.uuid4().hex
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers[REQUEST_ID_HEADER] = request_id
    response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response
