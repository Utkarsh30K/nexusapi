"""
Job API routes v1 - Original API

Provides endpoints for creating and managing background jobs.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, TokenPayload
from app.dependencies.rate_limit import check_rate_limit
from app.models.job import Job, JobStatus, JobType
from app.models.user import User
from app.services.job_service import JobService
from app.services.credit_service import CreditService
from app.worker import enqueue_job
import json


router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


# Pydantic models for request/response
class CreateJobRequest(BaseModel):
    """Request model for creating a job."""
    text: str
    job_type: str = "summarize"  # summarize or analyze


class JobResponse(BaseModel):
    """Response model for a job."""
    id: str
    org_id: str
    user_id: str
    job_type: str
    status: str
    input_data: str | None = None
    output_data: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    attempt_count: int = 0
    created_at: str
    
    class Config:
        from_attributes = True


def job_to_response(job: Job) -> JobResponse:
    """Convert Job model to JobResponse."""
    return JobResponse(
        id=job.id,
        org_id=job.org_id,
        user_id=job.user_id,
        job_type=job.job_type.value if isinstance(job.job_type, JobType) else job.job_type,
        status=job.status.value if isinstance(job.status, JobStatus) else job.status,
        input_data=job.input_data,
        output_data=job.output_data,
        error_message=job.error_message,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        attempt_count=job.attempt_count,
        created_at=job.created_at.isoformat() if job.created_at else None,
    )


async def get_user_from_token(
    token: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get User object from token payload."""
    stmt = select(User).where(User.id == token.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


@router.post("/summarize", response_model=dict)
async def create_summarize_job(
    request: CreateJobRequest,
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new summarize job (v1).
    
    Returns immediately with job_id (under 100ms).
    The actual processing happens in the background.
    """
    # Check rate limit
    await check_rate_limit(request, current_user.organisation_id)
    
    job_type_enum = JobType.SUMMARIZE if request.job_type == "summarize" else JobType.ANALYZE
    credits_required = 10 if request.job_type == "summarize" else 25
    
    # Check and deduct credits
    credit_service = CreditService(db)
    balance = await credit_service.get_balance(current_user.organisation_id)
    
    if balance < credits_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Balance: {balance}, Required: {credits_required}"
        )
    
    success = await credit_service.deduct_credits(
        org_id=current_user.organisation_id,
        amount=credits_required,
        job_id=None,
        description=f"Job creation: {request.job_type}"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deduct credits"
        )
    
    job_service = JobService(db)
    job = await job_service.create_job(
        org_id=current_user.organisation_id,
        user_id=current_user.id,
        job_type=job_type_enum,
        input_data=json.dumps({"text": request.text, "credits": credits_required})
    )
    
    try:
        await enqueue_job(request.job_type, job.id)
    except Exception as e:
        print(f"Failed to enqueue job: {e}")
    
    return {
        "job_id": job.id,
        "status": "pending",
        "message": f"Job created successfully. Credits deducted: {credits_required}"
    }


@router.post("/analyze", response_model=dict)
async def create_analyze_job(
    request: CreateJobRequest,
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new analyze job (v1)."""
    await check_rate_limit(request, current_user.organisation_id)
    
    credits_required = 25
    
    credit_service = CreditService(db)
    balance = await credit_service.get_balance(current_user.organisation_id)
    
    if balance < credits_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Balance: {balance}, Required: {credits_required}"
        )
    
    success = await credit_service.deduct_credits(
        org_id=current_user.organisation_id,
        amount=credits_required,
        job_id=None,
        description="Job creation: analyze"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deduct credits"
        )
    
    job_service = JobService(db)
    job = await job_service.create_job(
        org_id=current_user.organisation_id,
        user_id=current_user.id,
        job_type=JobType.ANALYZE,
        input_data=json.dumps({"text": request.text, "credits": credits_required})
    )
    
    try:
        await enqueue_job("analyze", job.id)
    except Exception as e:
        print(f"Failed to enqueue job: {e}")
    
    return {
        "job_id": job.id,
        "status": "pending",
        "message": f"Job created successfully. Credits deducted: {credits_required}"
    }


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Get job status and result by ID (v1)."""
    await check_rate_limit(None, current_user.organisation_id)
    
    job_service = JobService(db)
    job = await job_service.get_job_by_id_and_org(job_id, current_user.organisation_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job_to_response(job)


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """List all jobs for the user's organisation (v1)."""
    await check_rate_limit(None, current_user.organisation_id)
    
    job_service = JobService(db)
    jobs = await job_service.get_jobs_by_org(current_user.organisation_id)
    
    return [job_to_response(job) for job in jobs]
