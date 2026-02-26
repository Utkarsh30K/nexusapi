"""
Credit models.

Manages organisation credits and credit transactions for the multi-tenant system.
"""
import uuid
from sqlalchemy import String, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin


class TransactionType(str, enum.Enum):
    """Credit transaction type enum."""
    DEDUCTION = "deduction"
    REFUND = "refund"


class OrgCredit(Base, TimestampMixin):
    """
    Organisation credit balance model.
    
    Each organisation has exactly one credit balance record.
    """
    __tablename__ = "org_credits"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    organisation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    organisation = relationship("Organisation", back_populates="org_credits")

    def __repr__(self):
        return f"<OrgCredit(id={self.id}, org_id={self.organisation_id}, balance={self.balance})>"


class CreditTransaction(Base, TimestampMixin):
    """
    Credit transaction history model.
    
    Records all credit deductions and refunds for audit purposes.
    """
    __tablename__ = "credit_transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    organisation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, native_enum=False),
        nullable=False
    )
    job_id: Mapped[str] = mapped_column(String(36), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    organisation = relationship("Organisation", back_populates="credit_transactions")

    def __repr__(self):
        return f"<CreditTransaction(id={self.id}, org_id={self.organisation_id}, amount={self.amount}, type={self.type})>"
