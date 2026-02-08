"""
Service mode FastAPI application.
Use this to run open-skills as a standalone microservice (sidecar mode).

For library mode (embedded in your app), use:
    from open_skills.integrations.fastapi_integration import mount_open_skills
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from open_skills.service.api.router import router
from open_skills.config import get_settings
from open_skills.core.telemetry import logger
from open_skills.db.base import dispose_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for service mode.
    """
    settings = get_settings()
    logger.info(
        "openskills_service_startup",
        environment=settings.environment,
        version=settings.app_version,
        mode="service",
    )

    yield

    logger.info("openskills_service_shutdown")
    await dispose_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application (lazy initialization)."""
    settings = get_settings()

    # Create FastAPI application for service mode
    app = FastAPI(
        title=f"{settings.app_name} Service",
        version=settings.app_version,
        description="Open-Skills as a standalone microservice (sidecar mode)",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for unhandled errors."""
        logger.exception("unhandled_exception", error=str(exc), path=request.url.path)
        settings = get_settings()
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc) if settings.debug else None,
            },
        )

    # Include API router
    app.include_router(router)

    # Root endpoint
    @app.get("/")
    async def root():
        """Service information endpoint."""
        settings = get_settings()
        return {
            "name": f"{settings.app_name} Service",
            "version": settings.app_version,
            "mode": "service",
            "environment": settings.environment,
            "docs": "/docs" if settings.is_development else None,
        }

    return app


# Create app instance (will be lazy when imported as a module)
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "open_skills.service.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level=settings.log_level.lower(),
    )
