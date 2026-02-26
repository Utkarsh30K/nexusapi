"""
Job model for async background processing.

SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class JobStatus(str, enum.Enum):
    """Job status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, enum.Enum):
    """Job type enum."""
    SUMMARIZE = "summarize"
    ANALYZE = "analyze"


class Job(Base, TimestampMixin):
    """
    Job model for background processing.
    
    Represents a task that is queued and processed asynchronously.
    """
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    org_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    job_type: Mapped[JobType] = mapped_column(
        SQLEnum(JobType, native_enum=False, create_type=False),
        nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False, create_type=False),
        nullable=False,
        default=JobStatus.PENDING
    )
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"
