"""
Logging middleware for request/response logging.

Logs all HTTP requests with timing and context.
"""
import time
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests with timing and context.
    
    Adds: org_id, user_id, route, duration_ms, status to every log.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract user info from JWT if present (set by auth middleware)
        org_id = getattr(request.state, 'org_id', None)
        user_id = getattr(request.state, 'user_id', None)
        
        # Bind context to logger for this request
        request_logger = logger.bind(
            org_id=str(org_id) if org_id else None,
            user_id=str(user_id) if user_id else None,
            route=request.url.path,
            method=request.method,
        )
        
        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            request_logger.error(
                "request_failed",
                path=request.url.path,
                status_code=500,
                duration_ms=round(duration_ms, 2),
                error=str(e)
            )
            raise
        
        duration_ms = (time.time() - start_time) * 1000
        
        request_logger.info(
            "request_completed",
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        
        return response
