from __future__ import annotations

from fastapi import FastAPI
from httpx import AsyncClient

from app.api.routes.health import get_readiness_checks


async def _ok() -> None:
    return None


async def _boom() -> None:
    raise ConnectionError("down")


async def test_liveness_returns_envelope(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["app"] == "NutriAI"
    assert "error" not in body or body["error"] is None


async def test_liveness_sets_request_id_header(client: AsyncClient) -> None:
    resp = await client.get("/api/health", headers={"X-Request-ID": "abc123"})
    assert resp.headers["X-Request-ID"] == "abc123"
    assert resp.headers["Server-Timing"].startswith("app;dur=")


async def test_readiness_ok_when_dependencies_up(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_readiness_checks] = lambda: {"database": _ok, "redis": _ok}
    resp = await client.get("/api/health/ready")
    assert resp.status_code == 200
    assert resp.json()["data"]["checks"] == {"database": "ok", "redis": "ok"}


async def test_readiness_503_when_dependency_down(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_readiness_checks] = lambda: {"database": _ok, "redis": _boom}
    resp = await client.get("/api/health/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "service_unavailable"
    assert body["error"]["details"]["checks"] == {"database": "ok", "redis": "error"}


async def test_openapi_is_served(client: AsyncClient) -> None:
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "NutriAI API"
