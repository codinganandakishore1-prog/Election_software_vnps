"""Global exception handlers."""

from election_platform.schemas.response import APIResponse
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.base import AppException


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse.fail(message=exc.message).model_dump(),
        )

    @app.exception_handler(NotImplementedError)
    async def not_implemented_handler(_request: Request, exc: NotImplementedError) -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content=APIResponse.fail(message=str(exc) or "Not implemented").model_dump(),
        )
