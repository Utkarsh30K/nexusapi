"""
Credit API routes.

Provides endpoints for credit balance and transactions.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services.jwt_service import JWTService
from app.models.organisation import Organisation
from app.models.credit import OrgCredit, CreditTransaction


router = APIRouter(prefix="/api/credits", tags=["credits"])


async def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get current user from JWT in Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    jwt_service = JWTService()
    payload = jwt_service.verify_token(token)
    
    if not payload:
        return None
    
    return payload


@router.get("/", response_model=dict)
async def get_credits(
    token_data: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Get credit balance and transactions for the user's organisation."""
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    org_id = token_data.get("org_id")
    
    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
    # Get organisation
    org_stmt = select(Organisation).where(Organisation.id == org_id)
    org_result = await db.execute(org_stmt)
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=404,
            detail="Organisation not found"
        )
    
    # Get credit balance
    credit_stmt = select(OrgCredit).where(OrgCredit.organisation_id == org_id)
    credit_result = await db.execute(credit_stmt)
    credit = credit_result.scalar_one_or_none()
    
    balance = credit.balance if credit else 0
    
    # Get recent transactions
    txn_stmt = select(CreditTransaction).where(
        CreditTransaction.organisation_id == org_id
    ).order_by(CreditTransaction.created_at.desc()).limit(50)
    
    txn_result = await db.execute(txn_stmt)
    transactions = txn_result.scalars().all()
    
    return {
        "balance": balance,
        "organisation_name": org.name,
        "transactions": [
            {
                "id": str(t.id),
                "amount": t.amount,
                "type": t.type.value if hasattr(t.type, 'value') else str(t.type),
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]
    }
