from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_ISOLATED_VARS = ("ENVIRONMENT", "JWT_SECRET_KEY", "FIELD_ENCRYPTION_KEY", "DEBUG", "CORS_ORIGINS")


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _ISOLATED_VARS:
        monkeypatch.delenv(var, raising=False)


def _settings(**kwargs: object) -> Settings:
    return Settings(_env_file=None, **kwargs)  # type: ignore[call-arg]


def test_cors_origins_parsed_from_comma_list() -> None:
    s = _settings(cors_origins="http://a.com, http://b.com ,")
    assert s.cors_origin_list == ["http://a.com", "http://b.com"]


def test_development_allows_default_secret() -> None:
    s = _settings(environment="development")
    assert not s.is_production


def test_production_rejects_insecure_defaults() -> None:
    with pytest.raises(ValidationError) as exc:
        _settings(environment="production")
    msg = str(exc.value)
    assert "JWT_SECRET_KEY" in msg
    assert "FIELD_ENCRYPTION_KEY" in msg


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        _settings(
            environment="production",
            jwt_secret_key="x" * 48,
            field_encryption_key="k" * 44,
            cors_origins="*",
        )


def test_production_accepts_strong_config() -> None:
    s = _settings(
        environment="production",
        jwt_secret_key="x" * 48,
        field_encryption_key="k" * 44,
        cors_origins="https://nutriai.app",
    )
    assert s.is_production
