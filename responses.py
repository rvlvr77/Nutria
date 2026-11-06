"""Envelope estándar de respuesta: { success, data?, error?: {code, message} }."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str = Field(examples=["not_found"])
    message: str = Field(examples=["Recurso no encontrado"])
    details: Any | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorBody | None = None


def ok(data: T) -> ApiResponse[T]:
    return ApiResponse[T](success=True, data=data)


def fail(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    """Cuerpo JSON de error (dict ya serializable, usado por los exception handlers)."""
    body = ApiResponse[None](
        success=False, error=ErrorBody(code=code, message=message, details=details)
    )
    return body.model_dump(mode="json", exclude_none=True)
