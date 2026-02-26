"""
JWT token service for authentication.

SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import settings


class JWTService:
    """Service for creating and verifying JWT tokens."""
    
    def create_token(self, user_id: str, org_id: str, role: str, email: str) -> str:
        """
        Create a JWT token with user context.
        
        Args:
            user_id: User's unique ID
            org_id: Organisation ID
            role: User role (admin or member)
            email: User's email
            
        Returns:
            Encoded JWT token string
        """
        expires = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        
        payload = {
            "sub": user_id,
            "org_id": org_id,
            "role": role,
            "email": email,
            "exp": expires
        }
        
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> dict | None:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dict or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None
