from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from app.core.exceptions import (
    BusinessRuleError,
    NotFoundError,
    RateLimitError,
    register_exception_handlers,
)


class _Body(BaseModel):
    age: int = Field(ge=18)


@pytest.fixture
async def err_client() -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError("Plan no encontrado")

    @app.get("/rule")
    async def rule() -> None:
        raise BusinessRuleError("Requiere nutricionista", details={"rule": 2})

    @app.get("/limited")
    async def limited() -> None:
        raise RateLimitError("Límite diario alcanzado")

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secreto interno")

    @app.post("/validate")
    async def validate(body: _Body) -> _Body:
        return body

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_app_error_uses_envelope(err_client: AsyncClient) -> None:
    resp = await err_client.get("/not-found")
    assert resp.status_code == 404
    assert resp.json() == {
        "success": False,
        "error": {"code": "not_found", "message": "Plan no encontrado"},
    }


async def test_business_rule_error_includes_details(err_client: AsyncClient) -> None:
    resp = await err_client.get("/rule")
    assert resp.status_code == 422
    assert resp.json()["error"] == {
        "code": "business_rule_violation",
        "message": "Requiere nutricionista",
        "details": {"rule": 2},
    }


async def test_rate_limit_sets_retry_after(err_client: AsyncClient) -> None:
    resp = await err_client.get("/limited")
    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == "3600"


async def test_unhandled_error_hides_internals(err_client: AsyncClient) -> None:
    resp = await err_client.get("/crash")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "internal_error"
    assert "secreto" not in resp.text


async def test_validation_error_envelope(err_client: AsyncClient) -> None:
    resp = await err_client.post("/validate", json={"age": 12})
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"][0]["loc"] == ["body", "age"]


async def test_unknown_route_returns_enveloped_404(err_client: AsyncClient) -> None:
    resp = await err_client.get("/nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
