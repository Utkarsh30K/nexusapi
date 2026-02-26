"""
Organisation model.

Represents a tenant organisation in the multi-tenant system.
"""
import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Organisation(Base, TimestampMixin):
    """
    Organisation model representing a tenant in the system.
    
    Each organisation has its own users, credits, and data isolation.
    """
    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Relationships
    users = relationship(
        "User",
        back_populates="organisation",
        cascade="all, delete-orphan"
    )
    org_credits = relationship(
        "OrgCredit",
        back_populates="organisation",
        uselist=False
    )
    credit_transactions = relationship(
        "CreditTransaction",
        back_populates="organisation"
    )

    def __repr__(self):
        return f"<Organisation(id={self.id}, name={self.name}, domain={self.domain})>"
