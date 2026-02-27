"""
Job API routes.

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


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# Pydantic models for request/response
class CreateJobRequest(BaseModel):
    """Request model for creating a job."""
    text: str = ""
    job_type: str = "summarize"  # summarize or analyze


class CreateJobRequestV2(BaseModel):
    """Request model for creating a job (new API)."""
    job_type: str
    input_data: dict = {}


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


@router.post("", response_model=dict)
async def create_job_v2(
    request: CreateJobRequestV2,
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job (new API).
    
    Accepts job_type (SUMMARIZE/ANALYZE) and input_data dict.
    Returns immediately with job_id.
    """
    # Check rate limit
    await check_rate_limit(None, current_user.organisation_id)
    
    # Normalize job_type
    job_type_str = request.job_type.upper()
    
    # Map to enum
    if job_type_str == "SUMMARIZE":
        job_type_enum = JobType.SUMMARIZE
        credits_required = 10
    elif job_type_str == "ANALYZE":
        job_type_enum = JobType.ANALYZE
        credits_required = 25
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job_type: {request.job_type}. Use SUMMARIZE or ANALYZE."
        )
    
    # Check and deduct credits
    credit_service = CreditService(db)
    balance = await credit_service.get_balance(current_user.organisation_id)
    
    if balance < credits_required:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Balance: {balance}, Required: {credits_required}"
        )
    
    # Deduct credits
    success = await credit_service.deduct_credits(
        org_id=current_user.organisation_id,
        amount=credits_required,
        job_id=None,
        description=f"Job: {job_type_str}"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deduct credits"
        )
    
    # Prepare input data
    input_json = json.dumps({
        **request.input_data,
        "credits": credits_required
    })
    
    # Create job in database
    job_service = JobService(db)
    job = await job_service.create_job(
        org_id=current_user.organisation_id,
        user_id=current_user.id,
        job_type=job_type_enum,
        input_data=input_json
    )
    
    # Enqueue job for background processing
    try:
        await enqueue_job(job_type_str.lower(), job.id)
    except Exception as e:
        print(f"Failed to enqueue job: {e}")
    
    return {
        "id": job.id,
        "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
        "job_type": job_type_str,
        "input_data": request.input_data,
        "result": None,
        "error": None,
        "credits_deducted": credits_required,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "message": f"Job created successfully. Credits deducted: {credits_required}"
    }


@router.post("/summarize", response_model=dict)
async def create_summarize_job(
    request: CreateJobRequest,
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new summarize job.
    
    Returns immediately with job_id (under 100ms).
    The actual processing happens in the background.
    """
    # Task 3-2: Check rate limit (100 requests per 15 minutes per org)
    await check_rate_limit(request, current_user.organisation_id)
    
    # Map job_type string to JobType enum
    job_type_enum = JobType.SUMMARIZE if request.job_type == "summarize" else JobType.ANALYZE
    
    # Calculate credits based on job type
    credits_required = 10 if request.job_type == "summarize" else 25
    
    # Check and deduct credits (Task 4: Credit Deduction Safety)
    credit_service = CreditService(db)
    balance = await credit_service.get_balance(current_user.organisation_id)
    
    if balance < credits_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Balance: {balance}, Required: {credits_required}"
        )
    
    # Deduct credits
    success = await credit_service.deduct_credits(
        org_id=current_user.organisation_id,
        amount=credits_required,
        job_id=None,  # Will be set after job creation
        description=f"Job creation: {request.job_type}"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deduct credits"
        )
    
    # Create job in database
    job_service = JobService(db)
    job = await job_service.create_job(
        org_id=current_user.organisation_id,
        user_id=current_user.id,
        job_type=job_type_enum,
        input_data=json.dumps({"text": request.text, "credits": credits_required})
    )
    
    # Update transaction with job_id
    # (In a real system, we'd update the transaction record)
    
    # Enqueue job for background processing
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
    """
    Create a new analyze job.
    """
    # Task 3-2: Check rate limit (100 requests per 15 minutes per org)
    await check_rate_limit(request, current_user.organisation_id)
    
    job_type_enum = JobType.ANALYZE
    credits_required = 25
    
    # Check and deduct credits (Task 4: Credit Deduction Safety)
    credit_service = CreditService(db)
    balance = await credit_service.get_balance(current_user.organisation_id)
    
    if balance < credits_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Balance: {balance}, Required: {credits_required}"
        )
    
    # Deduct credits
    success = await credit_service.deduct_credits(
        org_id=current_user.organisation_id,
        amount=credits_required,
        job_id=None,
        description=f"Job creation: analyze"
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
        await enqueue_job("analyze", job.id)
    except Exception as e:
        print(f"Failed to enqueue job: {e}")
    
    return {
        "job_id": job.id,
        "status": "pending",
        "message": f"Job created successfully. Credits deducted: {credits_required}"
    }


@router.get("/{job_id}", response_model=dict)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job status and result by ID.
    """
    # Task 3-2: Check rate limit
    await check_rate_limit(None, current_user.organisation_id)
    
    job_service = JobService(db)
    job = await job_service.get_job_by_id_and_org(job_id, current_user.organisation_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Return in format expected by frontend
    return {
        "id": job.id,
        "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
        "job_type": job.job_type.value if isinstance(job.job_type, JobType) else job.job_type,
        "input_data": json.loads(job.input_data) if job.input_data else {},
        "result": job.output_data,
        "error": job.error_message,
        "credits_deducted": json.loads(job.input_data).get("credits", 0) if job.input_data else 0,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    List all jobs for the user's organisation.
    """
    # Task 3-2: Check rate limit
    await check_rate_limit(None, current_user.organisation_id)
    
    job_service = JobService(db)
    jobs = await job_service.get_jobs_by_org(current_user.organisation_id)
    
    return [job_to_response(job) for job in jobs]


# Test endpoint for retry logic demo
@router.post("/test-fail", response_model=dict)
async def create_failing_job(
    current_user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a test job that will always fail.
    Used to test retry logic (Task 3 demo gate) and credit refund (Task 4).
    """
    # Task 3-2: Check rate limit
    await check_rate_limit(None, current_user.organisation_id)
    
    credits_required = 10
    
    # Check and deduct credits (Task 4: Credit Deduction Safety)
    credit_service = CreditService(db)
    balance = await credit_service.get_balance(current_user.organisation_id)
    
    if balance < credits_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Balance: {balance}, Required: {credits_required}"
        )
    
    # Deduct credits
    success = await credit_service.deduct_credits(
        org_id=current_user.organisation_id,
        amount=credits_required,
        job_id=None,
        description="Test job: summarize (will fail)"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deduct credits"
        )
    
    # Create job with empty text which will cause failure
    job_service = JobService(db)
    job = await job_service.create_job(
        org_id=current_user.organisation_id,
        user_id=current_user.id,
        job_type=JobType.SUMMARIZE,
        input_data=json.dumps({"text": "", "credits": credits_required})  # Empty text = failure
    )
    
    # Enqueue job
    await enqueue_job("summarize", job.id)
    
    return {
        "job_id": job.id,
        "status": "pending",
        "message": f"Test failing job created. Credits: {credits_required} deducted. Worker will retry 3 times, then refund."
    }
