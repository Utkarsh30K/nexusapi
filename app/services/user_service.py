"""
SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole


class UserService:
    """Service for managing users within an organisation."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: str, org_id: str) -> User | None:
        """
        Get user by ID within a specific organisation.
        
        Args:
            user_id: User UUID
            org_id: Organisation UUID (required for security)
            
        Returns:
            User or None if not found
        """
        stmt = select(User).where(
            User.id == user_id,
            User.organisation_id == org_id  # SECURITY: Enforce org isolation
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str, org_id: str) -> User | None:
        """
        Get user by email within a specific organisation.
        
        Args:
            email: User email address
            org_id: Organisation UUID (required for security)
            
        Returns:
            User or None if not found
        """
        stmt = select(User).where(
            User.email == email,
            User.organisation_id == org_id  # SECURITY: Enforce org isolation
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_google_id(self, google_id: str) -> User | None:
        """
        Get user by Google ID (global search, not org-specific).
        
        Used for OAuth login - we need to find users across orgs.
        
        Args:
            google_id: Google OAuth user ID
            
        Returns:
            User or None if not found
        """
        stmt = select(User).where(User.google_id == google_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_by_org(self, org_id: str) -> list[User]:
        """
        Get all users in an organisation.
        
        Args:
            org_id: Organisation UUID
            
        Returns:
            List of users in the organisation
        """
        stmt = select(User).where(User.organisation_id == org_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(
        self,
        email: str,
        name: str,
        organisation_id: str,
        role: UserRole = UserRole.MEMBER,
        google_id: str | None = None
    ) -> User:
        """
        Create a new user in an organisation.
        
        Args:
            email: User email address
            name: User name
            organisation_id: Organisation UUID
            role: User role (default: MEMBER)
            google_id: Google OAuth ID (optional)
            
        Returns:
            Newly created User
        """
        user = User(
            email=email,
            name=name,
            organisation_id=organisation_id,
            role=role,
            google_id=google_id
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
