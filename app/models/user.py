"""
User model.

Represents a user belonging to an organisation with a specific role.
"""
import uuid
from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """User role enum for role-based access control."""
    ADMIN = "admin"
    MEMBER = "member"


class User(Base, TimestampMixin):
    """
    User model representing a user within an organisation.
    
    Each user belongs to exactly one organisation and has a role (admin or member).
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organisation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False, create_type=False),
        nullable=False,
        default=UserRole.MEMBER
    )
    google_id: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    organisation = relationship("Organisation", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, org_id={self.organisation_id}, role={self.role})>"
