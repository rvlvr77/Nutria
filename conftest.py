from __future__ import annotations

import os
from collections.abc import AsyncIterator

os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
