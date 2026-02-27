"""
Authentication routes for Google OAuth.

SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.oauth import oauth
from app.services.organisation_service import OrganisationService
from app.services.user_service import UserService
from app.services.credit_service import CreditService
from app.services.jwt_service import JWTService
from app.models.user import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    id_token: str


@router.post("/google")
async def google_login_with_token(
    request: GoogleTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth token from frontend.
    
    This endpoint:
    1. Validates Google ID token
    2. Gets user info from Google
    3. Creates organisation if needed (first user from domain)
    4. Creates/links user account
    5. Returns JWT in JSON body
    """
    try:
        # Verify the Google ID token using Google's tokeninfo endpoint
        async with httpx.AsyncClient() as client:
            # Use Google's tokeninfo endpoint to validate the ID token
            tokeninfo_response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={request.id_token}"
            )
            
            if tokeninfo_response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Google token"
                )
            
            user_info = tokeninfo_response.json()
        
        # Extract user data
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("sub")  # Google's unique user ID
        
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
            
            return {
                "status": "success",
                "message": "User logged in successfully",
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": existing_user.id,
                "email": existing_user.email,
                "organisation_id": str(existing_user.organisation_id),
                "role": existing_user.role.value
            }
        
        # New user - check if organisation exists for this domain
        organisation = await org_service.get_by_domain(domain)
        
        if not organisation:
            # Create new organisation for this domain
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
        
        return {
            "status": "success",
            "message": "User created successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "email": user.email,
            "organisation_id": str(organisation.id),
            "organisation_name": organisation.name,
            "role": user.role.value,
            "credits": 100 if user_role == UserRole.ADMIN else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/login/google")
async def login_google(request):
    """
    Redirect user to Google OAuth login page.
    """
    from starlette.requests import Request as StarletteRequest
    redirect_uri = str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(StarletteRequest(request._scope), redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback (server-side flow).
    """
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import RedirectResponse
    
    try:
        token = await oauth.google.authorize_access_token(StarletteRequest(request._scope))
        
        user_info = None
        
        if token.get("id_token"):
            try:
                user_info = await oauth.google.parse_id_token(StarletteRequest(request._scope), token)
            except Exception:
                pass
        
        if not user_info:
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
        
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("id") or user_info.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not provided by Google"
            )
        
        domain = email.split("@")[1]
        
        user_service = UserService(db)
        org_service = OrganisationService(db)
        credit_service = CreditService(db)
        
        existing_user = await user_service.get_by_google_id(google_id)
        
        jwt_service = JWTService()
        
        if existing_user:
            access_token = jwt_service.create_token(
                user_id=existing_user.id,
                org_id=existing_user.organisation_id,
                role=existing_user.role.value,
                email=existing_user.email
            )
            
            response = RedirectResponse(url="/")
            response.set_cookie(
                key="auth-token",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=60 * 60 * 24
            )
            return response
        
        organisation = await org_service.get_by_domain(domain)
        
        if not organisation:
            company_name = domain.split(".")[0].title()
            
            organisation = await org_service.create(
                name=f"{company_name} Organisation",
                domain=domain
            )
            
            await credit_service.create_credit(
                org_id=organisation.id,
                initial_balance=100
            )
            
            user_role = UserRole.ADMIN
        else:
            user_role = UserRole.MEMBER
        
        user = await user_service.create(
            email=email,
            name=name,
            organisation_id=organisation.id,
            role=user_role,
            google_id=google_id
        )
        
        access_token = jwt_service.create_token(
            user_id=user.id,
            org_id=organisation.id,
            role=user.role.value,
            email=user.email
        )
        
        response = RedirectResponse(url="/")
        response.set_cookie(
            key="auth-token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24
        )
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    """
    return {"status": "success", "message": "Logged out"}


@router.get("/me")
async def get_current_user():
    """
    Get current user info.
    """
    return {
        "message": "This endpoint will require JWT authentication",
        "status": "not_implemented"
    }
