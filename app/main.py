"""
NexusAPI - Multi-tenant backend platform

FastAPI application entry point.
"""
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.routes.auth import router as auth_router
from app.routes.api import router as api_router

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant backend platform for organisations to manage users and AI-powered endpoints",
)

# Add SessionMiddleware for OAuth (required by Authlib)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,
)

# Include authentication routes
app.include_router(auth_router)

# Include API routes
app.include_router(api_router)


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
