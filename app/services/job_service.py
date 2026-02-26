"""
Job service for background job management.

SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job, JobStatus, JobType


class JobService:
    """Service for managing background jobs."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_job(
        self,
        org_id: str,
        user_id: str,
        job_type: JobType,
        input_data: str
    ) -> Job:
        """
        Create a new job in PENDING status.
        
        Args:
            org_id: Organisation ID
            user_id: User ID who created the job
            job_type: Type of job (summarize, analyze)
            input_data: JSON string of input data
            
        Returns:
            Newly created Job
        """
        job = Job(
            org_id=org_id,
            user_id=user_id,
            job_type=job_type,
            input_data=input_data,
            status=JobStatus.PENDING
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def claim_job(self, job_id: str) -> Job | None:
        """
        Mark a job as RUNNING (claim it for processing).
        
        Args:
            job_id: Job UUID
            
        Returns:
            Job if successfully claimed, None if not found or not pending
        """
        job = await self.get_job_by_id(job_id)
        if not job or job.status != JobStatus.PENDING:
            return None
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.attempt_count += 1
        
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def complete_job(self, job_id: str, output_data: str) -> Job | None:
        """
        Mark a job as COMPLETED with output.
        
        Args:
            job_id: Job UUID
            output_data: JSON string of output
            
        Returns:
            Job if successfully completed, None if not found
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.status = JobStatus.COMPLETED
        job.output_data = output_data
        job.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def fail_job(self, job_id: str, error_message: str) -> Job | None:
        """
        Mark a job as FAILED with error.
        
        Args:
            job_id: Job UUID
            error_message: Error description
            
        Returns:
            Job if exists, None if not found
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def get_job_by_id(self, job_id: str) -> Job | None:
        """Get job by ID."""
        stmt = select(Job).where(Job.id == job_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_job_by_id_and_org(self, job_id: str, org_id: str) -> Job | None:
        """Get job by ID within organisation."""
        stmt = select(Job).where(
            Job.id == job_id,
            Job.org_id == org_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_jobs_by_org(self, org_id: str) -> list[Job]:
        """Get all jobs for an organisation."""
        stmt = select(Job).where(Job.org_id == org_id).order_by(Job.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
