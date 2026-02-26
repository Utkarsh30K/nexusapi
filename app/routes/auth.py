"""
Authentication routes for Google OAuth.

SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from app.database import get_db
from app.oauth import oauth
from app.services.organisation_service import OrganisationService
from app.services.user_service import UserService
from app.services.credit_service import CreditService
from app.services.jwt_service import JWTService
from app.models.user import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login/google")
async def login_google(request: Request):
    """
    Redirect user to Google OAuth login page.
    
    Usage: Navigate to this endpoint to start OAuth flow.
    """
    # Build redirect URI - must match Google Console settings
    redirect_uri = str(request.url_for("google_callback"))
    
    # Redirect to Google
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    
    This endpoint:
    1. Exchanges authorization code for tokens
    2. Gets user info from Google
    3. Creates organisation if needed (first user from domain)
    4. Creates/links user account
    """
    try:
        # Exchange authorization code for tokens
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google - try parse_id_token first, fallback to userinfo
        user_info = None
        
        # Try to get id_token from token
        if token.get("id_token"):
            try:
                user_info = await oauth.google.parse_id_token(request, token)
            except Exception:
                pass
        
        # If parse_id_token failed or no id_token, fetch from userinfo endpoint
        if not user_info:
            # Make a request to Google's userinfo endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token['access_token']}"}
                )
                if response.status_code == 200:
                    user_info = response.json()
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to get user info from Google"
                    )
        
        if not user_info:
            raise HTTPException(
                status_code=400, 
                detail="Failed to get user info from Google"
            )
        
        # Extract user data
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("id") or user_info.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not provided by Google"
            )
        
        # Extract domain from email
        domain = email.split("@")[1]
        
        # Initialize services
        user_service = UserService(db)
        org_service = OrganisationService(db)
        credit_service = CreditService(db)
        
        # Check if user already exists (by Google ID)
        existing_user = await user_service.get_by_google_id(google_id)
        
        # Generate JWT token
        jwt_service = JWTService()
        
        if existing_user:
            # User already exists - log them in with JWT
            access_token = jwt_service.create_token(
                user_id=existing_user.id,
                org_id=existing_user.organisation_id,
                role=existing_user.role.value,
                email=existing_user.email
            )
            
            return JSONResponse({
                "status": "success",
                "message": "User logged in successfully",
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": existing_user.id,
                "email": existing_user.email,
                "organisation_id": existing_user.organisation_id,
                "role": existing_user.role.value
            })
        
        # New user - check if organisation exists for this domain
        organisation = await org_service.get_by_domain(domain)
        
        if not organisation:
            # Create new organisation for this domain
            # Extract company name from domain (e.g., "acme.com" -> "Acme")
            company_name = domain.split(".")[0].title()
            
            organisation = await org_service.create(
                name=f"{company_name} Organisation",
                domain=domain
            )
            
            # Create credit record for new organisation (100 free credits)
            await credit_service.create_credit(
                org_id=organisation.id,
                initial_balance=100
            )
            
            # First user from domain becomes admin
            user_role = UserRole.ADMIN
        else:
            # Existing organisation - user becomes member
            user_role = UserRole.MEMBER
        
        # Create new user
        user = await user_service.create(
            email=email,
            name=name,
            organisation_id=organisation.id,
            role=user_role,
            google_id=google_id
        )
        
        # Generate JWT token for new user
        access_token = jwt_service.create_token(
            user_id=user.id,
            org_id=organisation.id,
            role=user.role.value,
            email=user.email
        )
        
        return JSONResponse({
            "status": "success",
            "message": "User created successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "organisation_id": organisation.id,
            "organisation_name": organisation.name,
            "role": user.role.value,
            "credits": 100 if user_role == UserRole.ADMIN else 0
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    
    TODO: Implement JWT blacklisting in Task 4
    """
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me")
async def get_current_user():
    """
    Get current user info.
    
    TODO: Implement with JWT authentication in Task 4
    """
    return {
        "message": "This endpoint will require JWT authentication in Task 4",
        "status": "not_implemented"
    }
