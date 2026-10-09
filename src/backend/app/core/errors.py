"""Forma única de error {error:{code,message,details?}} + mapa de estados."""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)

_STATUS_TO_CODE = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "unprocessable_entity",
    500: "internal_error",
}


def error_body(status: int, message: str, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": _STATUS_TO_CODE.get(status, "error"), "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.status_code, str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content=error_body(422, "Entidad no procesable", details=exc.errors()))

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("error no manejado", extra={"path": str(request.url.path)})
        return JSONResponse(status_code=500, content=error_body(500, "Error interno del servidor"))
