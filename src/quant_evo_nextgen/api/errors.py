from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def status_code_for_value_error(error: ValueError) -> int:
    message = str(error).lower()
    if "not found" in message:
        return 404
    if "already" in message or "requires approval" in message or "not applyable" in message:
        return 409
    return 400


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status_code_for_value_error(exc),
        content={"detail": str(exc)},
    )
