"""
Webhook API routes.

Provides endpoints for registering webhook URLs per organisation.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, TokenPayload
from app.models.organisation import Organisation
from app.models.user import User


router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class SetWebhookRequest(BaseModel):
    """Request model for setting webhook URL."""
    url: str
    secret: str


@router.post("/", response_model=dict)
async def set_webhook(
    request: SetWebhookRequest,
    token: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set webhook URL for the organisation.
    
    The webhook will receive POST requests when jobs complete or fail.
    """
    # Get user's organisation
    stmt = select(User).where(User.id == token.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Update organisation webhook
    org_stmt = select(Organisation).where(Organisation.id == user.organisation_id)
    org_result = await db.execute(org_stmt)
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )
    
    org.webhook_url = request.url
    org.webhook_secret = request.secret
    await db.commit()
    
    return {
        "message": "Webhook configured successfully",
        "url": request.url
    }


@router.get("/", response_model=dict)
async def get_webhook(
    token: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current webhook configuration for the organisation."""
    # Get user's organisation
    stmt = select(User).where(User.id == token.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    org_stmt = select(Organisation).where(Organisation.id == user.organisation_id)
    org_result = await db.execute(org_stmt)
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )
    
    return {
        "url": org.webhook_url,
        "configured": org.webhook_url is not None
    }


@router.delete("/", response_model=dict)
async def delete_webhook(
    token: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove webhook configuration for the organisation."""
    # Get user's organisation
    stmt = select(User).where(User.id == token.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    org_stmt = select(Organisation).where(Organisation.id == user.organisation_id)
    org_result = await db.execute(org_stmt)
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )
    
    org.webhook_url = None
    org.webhook_secret = None
    await db.commit()
    
    return {"message": "Webhook removed successfully"}
