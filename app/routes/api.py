"""
API routes demonstrating role-based access control.

SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user, require_admin, TokenPayload

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/public")
async def public_endpoint():
    """
    Public endpoint - no auth required.
    
    Anyone can access this endpoint.
    """
    return {"message": "This is a public endpoint"}


@router.get("/authenticated")
async def authenticated_endpoint(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Authenticated endpoint - any valid token.
    
    Returns user info from JWT. Requires valid JWT token.
    """
    return {
        "message": "This is an authenticated endpoint",
        "user": {
            "id": current_user.sub,
            "org_id": current_user.org_id,
            "role": current_user.role,
            "email": current_user.email
        }
    }


@router.get("/admin-only")
async def admin_only_endpoint(
    admin_user: TokenPayload = Depends(require_admin)
):
    """
    Admin-only endpoint - requires admin role.
    
    Returns admin-specific data. Only admins can access.
    """
    return {
        "message": "This is an admin-only endpoint",
        "admin": {
            "id": admin_user.sub,
            "org_id": admin_user.org_id,
            "role": admin_user.role
        }
    }


@router.get("/org-data")
async def get_org_data(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get organisation data.
    
    SECURITY: This demonstrates org isolation - users can only
    access their own organisation's data.
    """
    return {
        "message": f"Data for organisation {current_user.org_id}",
        "org_id": current_user.org_id,
        "user_role": current_user.role
    }
