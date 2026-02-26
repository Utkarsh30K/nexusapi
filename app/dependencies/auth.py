"""
Authentication dependencies for FastAPI.

SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.services.jwt_service import JWTService


# Security scheme
security = HTTPBearer()


class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: str      # user_id
    org_id: str
    role: str
    email: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """
    Dependency that requires valid JWT token.
    
    Returns token payload if valid, raises 401 if invalid.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenPayload = Depends(get_current_user)):
            ...
    """
    jwt_service = JWTService()
    
    payload = jwt_service.verify_token(credentials.credentials)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenPayload(**payload)


def require_admin(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """
    Dependency that requires admin role.
    
    Returns user if admin, raises 403 if member.
    
    Usage:
        @app.get("/admin")
        async def admin_route(user: TokenPayload = Depends(require_admin)):
            ...
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
