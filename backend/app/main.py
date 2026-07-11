"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.logging import init_logging
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import api_router
from app.routers import health as health_router
from app.websocket.routes import register_websocket_routes


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    init_logging()
    for folder in (settings.upload_folder, settings.report_folder, settings.backup_folder, settings.log_folder):
        folder.mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)

    register_exception_handlers(app)
    register_websocket_routes(app)

    app.include_router(health_router.router, tags=["Health"])
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/")
    async def root() -> dict:
        return {"name": settings.app_name, "version": settings.app_version, "status": "running"}

    return app


app = create_app()
