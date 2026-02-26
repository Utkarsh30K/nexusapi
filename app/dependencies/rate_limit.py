"""
Rate limit dependency for FastAPI routes.
"""
from fastapi import Request, HTTPException, Depends
from app.services.rate_limiter import rate_limiter


async def check_rate_limit(request: Request, org_id: str):
    """
    Check rate limit for the organisation.
    
    Raises 429 if limit exceeded.
    """
    allowed, retry_after = await rate_limiter.is_allowed(org_id)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )
