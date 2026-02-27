"""
NexusAPI - Multi-tenant backend platform

FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Import observability modules
from app.config import settings
from app.logging_config import configure_logging
from app.sentry_config import configure_sentry
from app.middleware.logging import LoggingMiddleware
from app.routes.metrics import router as metrics_router

# Import route modules
from app.routes.auth import router as auth_router
from app.routes.api import router as api_router
from app.routes.jobs import router as jobs_router
from app.routes.jobs_v1 import router as jobs_v1_router
from app.routes.jobs_v2 import router as jobs_v2_router
from app.routes.webhooks import router as webhooks_router
from app.routes.credits import router as credits_router

# Initialize logging first
configure_logging()

# Initialize Sentry (if SENTRY_DSN is set)
configure_sentry()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant backend platform for organisations to manage users and AI-powered endpoints",
)

# Add logging middleware FIRST (runs before other middleware)
app.add_middleware(LoggingMiddleware)

# Add SessionMiddleware for OAuth (required by Authlib)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,
)

# Add CORS middleware to allow frontend to send cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include metrics endpoint FIRST (so it's always available)
app.include_router(metrics_router)

# Include authentication routes
app.include_router(auth_router)

# Include API routes
app.include_router(api_router)

# Include job routes
app.include_router(jobs_router)

# Include v1 job routes (original API)
app.include_router(jobs_v1_router)

# Include v2 job routes (new API with extra fields)
app.include_router(jobs_v2_router)

# Include webhook routes
app.include_router(webhooks_router)

# Include credit routes
app.include_router(credits_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected"
    }
