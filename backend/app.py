"""FastAPI application factory for AI-OS."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from .config import AppSettings, get_settings
from .dependencies import get_security_service
from .logging import configure_logging, get_logger
from .schemas import HealthResponse, LoginRequest, TokenResponse


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    app_settings = settings or get_settings()
    configure_logging(app_settings)
    logger = get_logger(bind={"component": "api"})

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        logger.info("Starting AI-OS backend", app=app_settings.app_name, env=app_settings.app_env)
        try:
            yield
        finally:
            logger.info("Stopping AI-OS backend")

    app = FastAPI(
        title=app_settings.app_name,
        description="AI-OS backend API",
        version="1.0.0",
        debug=app_settings.debug,
        lifespan=lifespan,
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health_check() -> HealthResponse:
        return HealthResponse(
            app_name=app_settings.app_name,
            environment=app_settings.app_env,
            timestamp=datetime.now(timezone.utc),
        )

    @app.post("/auth/token", response_model=TokenResponse, tags=["auth"])
    async def login(request: LoginRequest) -> TokenResponse:
        # This endpoint is ready for integration with the user repository once the database layer lands.
        if not request.username or not request.password:
            raise HTTPException(status_code=400, detail="Username and password are required.")

        access_token = get_security_service().create_access_token(request.username, role="user")
        return TokenResponse(access_token=access_token)

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"status": "AI-OS running", "version": "1.0.0"}

    return app
