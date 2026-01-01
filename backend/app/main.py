"""
FastAPI application entry point.
Configures the application with all routes, middleware, and lifecycle handlers.
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, close_db, check_db_connection
from app.utils.logging import configure_logging, get_logger, bind_context, clear_context

from app.api.v1.router import api_router


# Configure logging on module load
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize DB, create directories, log configuration
    - Shutdown: Close DB connections, cleanup resources
    """
    # Startup
    logger.info("Starting application...", debug=settings.debug)

    # Create static directories if they don't exit
    static_path = Path(settings.static_dir)
    for subdir in ["audio", "videos", "previews"]:
        (static_path / subdir).mkdir(parents=True, exist_ok=True)
    logger.info("Static directories initialized.", path=str(static_path))

    # Initialize database (in production, use Alembic migrations)
    if settings.debug:
        # Only auto-create tables in development
        # Production should use: alembic upgrade head
        pass  # Tables are created by init.sql in Docker

    # Built-in scheduler (disabled by default - use n8n instead)
    # Set SCHEDULER_ENABLED=true in .env to enable built-in scheduler
    from app.services.scheduler_service import start_scheduler, stop_scheduler
    import os

    if os.environ.get("SCHEDULER_ENABLED", "false").lower() == "true":
        await start_scheduler()
        logger.info("Built-in scheduler initialized")

    logger.info("Application startup complete")

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down application")

    # Stop scheduler if it was started
    if os.environ.get("SCHEDULER_ENABLED", "false").lower() == "true":
        stop_scheduler()

    await close_db()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered video generation and YouTube upload automation",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_prefix)

# === MIDDLEWARE ===

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all requests and bind context.

    Logs request method, path, and response status.
    Binds request_id for tracing.
    """
    import uuid

    request_id = str(uuid.uuid4())[:8]
    bind_context(request_id=request_id)

    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
    )

    try:
        response = await call_next(request)
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response
    except Exception as e:
        logger.exception(
            "Request failed", method=request.method, path=request.url.path, error=str(e)
        )
        raise
    finally:
        clear_context()


# === STATIC FILES ===

# Mount static files directory for serving generated media
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


# === HEALTH CHECK ===


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns 200 OK if database is reachable, 503 otherwise.
    Used by Docker health checks and load balancers.
    """
    db_healthy = await check_db_connection()

    if db_healthy:
        return {"status": "healthy", "database": "connected", "version": "1.0.0"}
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
            },
        )


# === API ROUTES ===

# Import and include API routers
# These will be created in subsequent sections
# from app.api.v1.router import api_router
# app.include_router(api_router, prefix=settings.api_v1_prefix)


# === ROOT ENDPOINT ===


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Disabled in production",
        "health": "/health",
    }


# === EXCEPTION HANDLERS ===


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors with 400 response."""
    logger.warning("Validation error", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with 500 response."""
    logger.exception("Unhandled exception", error=str(exc), path=request.url.path)

    if settings.debug:
        # Include error details in development
        return JSONResponse(
            status_code=500, content={"detail": str(exc), "type": type(exc).__name__}
        )
    else:
        # Hide details in production
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
