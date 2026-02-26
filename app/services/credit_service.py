"""
SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.credit import OrgCredit, CreditTransaction, TransactionType


class CreditService:
    """Service for managing organisation credits and transactions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_balance(self, org_id: str) -> int:
        """
        Get credit balance for an organisation.
        
        Args:
            org_id: Organisation UUID
            
        Returns:
            Credit balance (0 if no credits exist)
        """
        stmt = select(OrgCredit).where(OrgCredit.organisation_id == org_id)
        result = await self.db.execute(stmt)
        credit = result.scalar_one_or_none()
        return credit.balance if credit else 0
    
    async def get_credit_record(self, org_id: str) -> OrgCredit | None:
        """
        Get credit record for an organisation.
        
        Args:
            org_id: Organisation UUID
            
        Returns:
            OrgCredit or None if not found
        """
        stmt = select(OrgCredit).where(OrgCredit.organisation_id == org_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_credit(self, org_id: str, initial_balance: int = 0) -> OrgCredit:
        """
        Create credit record for an organisation.
        
        Args:
            org_id: Organisation UUID
            initial_balance: Initial credit balance (default: 0)
            
        Returns:
            Newly created OrgCredit
        """
        credit = OrgCredit(organisation_id=org_id, balance=initial_balance)
        self.db.add(credit)
        await self.db.commit()
        await self.db.refresh(credit)
        return credit
    
    async def deduct_credits(
        self,
        org_id: str,
        amount: int,
        job_id: str | None = None,
        description: str | None = None
    ) -> bool:
        """
        Deduct credits from an organisation's balance.
        
        Args:
            org_id: Organisation UUID
            amount: Amount to deduct
            job_id: Associated job ID (optional)
            description: Transaction description (optional)
            
        Returns:
            True if deduction successful, False if insufficient credits
        """
        # Get current credit record
        credit = await self.get_credit_record(org_id)
        if not credit or credit.balance < amount:
            return False
        
        # Deduct credits
        credit.balance -= amount
        
        # Record transaction
        transaction = CreditTransaction(
            organisation_id=org_id,
            amount=amount,
            type=TransactionType.DEDUCTION,
            job_id=job_id,
            description=description
        )
        self.db.add(transaction)
        
        await self.db.commit()
        return True
    
    async def refund_credits(
        self,
        org_id: str,
        amount: int,
        job_id: str | None = None,
        description: str | None = None
    ) -> bool:
        """
        Refund credits to an organisation's balance.
        
        Args:
            org_id: Organisation UUID
            amount: Amount to refund
            job_id: Associated job ID (optional)
            description: Transaction description (optional)
            
        Returns:
            True if refund successful, False otherwise
        """
        # Get current credit record
        credit = await self.get_credit_record(org_id)
        if not credit:
            return False
        
        # Add credits
        credit.balance += amount
        
        # Record transaction
        transaction = CreditTransaction(
            organisation_id=org_id,
            amount=amount,
            type=TransactionType.REFUND,
            job_id=job_id,
            description=description
        )
        self.db.add(transaction)
        
        await self.db.commit()
        return True
    
    async def get_transactions(self, org_id: str, limit: int = 10) -> list[CreditTransaction]:
        """
        Get credit transactions for an organisation.
        
        Args:
            org_id: Organisation UUID
            limit: Maximum number of transactions to return
            
        Returns:
            List of credit transactions (most recent first)
        """
        stmt = (
            select(CreditTransaction)
            .where(CreditTransaction.organisation_id == org_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
