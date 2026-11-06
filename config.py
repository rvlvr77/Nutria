"""Configuración central leída de variables de entorno (.env)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_SECRET = "change-me-in-production"  # noqa: S105 - valor centinela, se rechaza en prod


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "NutriAI"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000"

    # --- Infra ---
    database_url: str = "postgresql+asyncpg://nutriai:nutriai@localhost:5432/nutriai"
    database_echo: bool = False
    redis_url: str = "redis://localhost:6379/0"
    healthcheck_timeout_s: float = Field(default=2.0, gt=0, le=10)

    # --- Auth (se usa desde el Módulo 2) ---
    jwt_secret_key: SecretStr = SecretStr(_INSECURE_DEFAULT_SECRET)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_ttl_minutes: int = Field(default=15, gt=0)
    refresh_token_ttl_days: int = Field(default=7, gt=0)
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: str = "http://localhost:3000/auth/callback/google"

    # --- Cifrado de columnas sensibles (medical_conditions) ---
    field_encryption_key: SecretStr = SecretStr("")

    # --- USDA FoodData Central (Módulo 5) ---
    usda_api_key: SecretStr = SecretStr("")
    usda_base_url: str = "https://api.nal.usda.gov/fdc/v1"
    usda_rate_limit_per_hour: int = Field(default=1000, gt=0)
    usda_food_cache_ttl_days: int = Field(default=30, gt=0)
    usda_search_cache_ttl_days: int = Field(default=7, gt=0)

    # --- LLM (Módulo 7) ---
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o"
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = "llama-3.1-70b-versatile"
    llm_timeout_s: float = Field(default=30.0, gt=0)
    llm_temperature: float = Field(default=0.7, ge=0, le=2)
    llm_max_tokens: int = Field(default=2000, gt=0)

    # --- Reglas de negocio ---
    plan_generations_per_day: int = Field(default=10, gt=0)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> Settings:
        if not self.is_production:
            return self
        problems: list[str] = []
        secret = self.jwt_secret_key.get_secret_value()
        if secret == _INSECURE_DEFAULT_SECRET or len(secret) < 32:
            problems.append("JWT_SECRET_KEY debe definirse y tener >= 32 caracteres")
        if not self.field_encryption_key.get_secret_value():
            problems.append("FIELD_ENCRYPTION_KEY es obligatoria en producción")
        if self.debug:
            problems.append("DEBUG debe ser false en producción")
        if "*" in self.cors_origin_list:
            problems.append("CORS_ORIGINS no puede ser '*' en producción")
        if problems:
            raise ValueError("Configuración insegura para producción: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
