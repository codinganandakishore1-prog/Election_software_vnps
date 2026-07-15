"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from election_platform.logging.setup import get_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.logging import init_logging
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.csrf import CSRFMiddleware
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import api_router
from app.routers import health as health_router
from app.websocket.routes import register_websocket_routes

logger = get_logger("backend.application")

DEFAULT_THEME_ASSETS = Path(__file__).resolve().parent / "assets" / "default_theme"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    init_logging()
    for folder in (
        settings.upload_folder,
        settings.report_folder,
        settings.backup_folder,
        settings.config_package_folder,
        settings.log_folder,
    ):
        folder.mkdir(parents=True, exist_ok=True)

    # Verify upload root is writable (critical on Render persistent disks).
    probe = settings.upload_folder / ".write_test"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        logger.error("Upload folder is not writable (%s): %s", settings.upload_folder, exc)
        raise

    if settings.database_url.startswith("sqlite") or settings.bootstrap_database:
        from app.database.init_db import initialize_database

        bootstrap = initialize_database(seed=True) or {}
        logger.info("Database bootstrap complete: %s", bootstrap)

    logger.info(
        "Started %s v%s env=%s upload_folder=%s",
        settings.app_name,
        settings.app_version,
        settings.environment,
        settings.upload_folder,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=None if settings.is_production and not settings.debug else "/docs",
        redoc_url=None if settings.is_production and not settings.debug else "/redoc",
        openapi_url=None if settings.is_production and not settings.debug else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)

    register_exception_handlers(app)
    register_websocket_routes(app)

    app.include_router(health_router.router, tags=["Health"])
    app.include_router(api_router, prefix=settings.api_prefix)

    if DEFAULT_THEME_ASSETS.is_dir():
        app.mount(
            "/static/default-theme",
            StaticFiles(directory=str(DEFAULT_THEME_ASSETS)),
            name="default_theme",
        )

    @app.get("/")
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "environment": settings.environment,
        }

    return app


app = create_app()
