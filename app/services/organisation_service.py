"""
SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import Organisation


class OrganisationService:
    """Service for managing organisations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, org_id: str) -> Organisation | None:
        """
        Get organisation by ID.
        
        Args:
            org_id: Organisation UUID
            
        Returns:
            Organisation or None if not found
        """
        stmt = select(Organisation).where(Organisation.id == org_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_domain(self, domain: str) -> Organisation | None:
        """
        Get organisation by domain.
        
        Args:
            domain: Organisation domain (e.g., "acme.com")
            
        Returns:
            Organisation or None if not found
        """
        stmt = select(Organisation).where(Organisation.domain == domain)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, name: str, domain: str) -> Organisation:
        """
        Create a new organisation.
        
        Args:
            name: Organisation name
            domain: Organisation domain
            
        Returns:
            Newly created Organisation
        """
        org = Organisation(name=name, domain=domain)
        self.db.add(org)
        await self.db.commit()
        await self.db.refresh(org)
        return org
