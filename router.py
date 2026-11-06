"""Router raíz de la API. Cada módulo registra aquí su router (/auth, /profile, ...)."""

from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)
