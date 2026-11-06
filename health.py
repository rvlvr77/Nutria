"""Endpoints de salud: liveness (/health) y readiness (/health/ready)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.exceptions import ServiceUnavailableError
from app.core.redis import get_redis
from app.core.responses import ApiResponse, ok
from app.db.session import get_engine

logger = logging.getLogger("nutriai.health")
router = APIRouter(prefix="/health", tags=["health"])

CheckFn = Callable[[], Awaitable[None]]
CheckStatus = Literal["ok", "error"]


class LivenessData(BaseModel):
    status: Literal["ok"]
    app: str
    version: str
    environment: str


class ReadinessData(BaseModel):
    status: Literal["ok"]
    checks: dict[str, CheckStatus]


async def _check_database() -> None:
    async with get_engine().connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _check_redis() -> None:
    pong = await get_redis().ping()
    if not pong:
        raise RuntimeError("Redis no respondió PONG")


def get_readiness_checks() -> dict[str, CheckFn]:
    """Dependencia sobrescribible en tests."""
    return {"database": _check_database, "redis": _check_redis}


@router.get("", response_model=ApiResponse[LivenessData], summary="Liveness")
async def liveness(settings: Settings = Depends(get_settings)) -> ApiResponse[LivenessData]:
    return ok(
        LivenessData(
            status="ok",
            app=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )
    )


@router.get(
    "/ready",
    response_model=ApiResponse[ReadinessData],
    summary="Readiness (Postgres + Redis)",
    responses={503: {"model": ApiResponse[None]}},
)
async def readiness(
    checks: dict[str, CheckFn] = Depends(get_readiness_checks),
    settings: Settings = Depends(get_settings),
) -> ApiResponse[ReadinessData]:
    async def run(name: str, fn: CheckFn) -> tuple[str, CheckStatus]:
        try:
            await asyncio.wait_for(fn(), timeout=settings.healthcheck_timeout_s)
            return name, "ok"
        except Exception as exc:  # noqa: BLE001 - reportamos cualquier fallo de dependencia
            logger.warning("readiness check failed name=%s error=%r", name, exc)
            return name, "error"

    results = dict(await asyncio.gather(*(run(n, f) for n, f in checks.items())))
    if any(v == "error" for v in results.values()):
        raise ServiceUnavailableError("Dependencias no disponibles", details={"checks": results})
    return ok(ReadinessData(status="ok", checks=results))
