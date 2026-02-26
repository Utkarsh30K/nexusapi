"""
ARQ Background Worker for NexusAPI.

Processes jobs asynchronously using Redis queue.
"""
import json
import asyncio
from datetime import datetime

import google.generativeai as genai
from arq import ArqRedis, Retry
from arq.connections import RedisSettings

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.job import Job, JobStatus
from app.models.organisation import Organisation
from app.models.user import User
from app.models.credit import OrgCredit, CreditTransaction, TransactionType
from sqlalchemy import select


# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


async def process_summarize_job(ctx: dict, job_id: str) -> dict:
    """Process a summarize job using Gemini."""
    # ARQ uses job_try (starts at 1) and max_tries in context
    job_try = ctx.get("job_try", 1)
    max_tries = ctx.get("max_tries", 3)
    
    print(f"Processing summarize job: {job_id} (Attempt {job_try}/{max_tries})")
    
    async with AsyncSessionLocal() as db:
        stmt = select(Job).where(Job.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.attempt_count = job_try
        await db.commit()
        
        try:
            input_data = json.loads(job.input_data)
            text = input_data.get("text", "")
            
            if not text:
                raise ValueError("No text provided")
            
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(f"Summarize this: {text}")
            summary = response.text
            
            job.status = JobStatus.COMPLETED
            job.output_data = json.dumps({"summary": summary})
            job.completed_at = datetime.utcnow()
            await db.commit()
            
            return {"status": "completed", "summary": summary}
        except Exception as e:
            error_message = str(e)
            print(f"Job {job_id} failed: {error_message}")
            
            # Check if this is the last retry
            if job_try >= max_tries:
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.completed_at = datetime.utcnow()
                print(f"Job {job_id} permanently failed after {job_try} attempts")
                
                # Task 4: Refund credits on permanent failure
                input_data = json.loads(job.input_data)
                credits_to_refund = input_data.get("credits", 0)
                
                if credits_to_refund > 0:
                    # Get credit record and add refund
                    credit_stmt = select(OrgCredit).where(OrgCredit.organisation_id == job.org_id)
                    credit_result = await db.execute(credit_stmt)
                    credit = credit_result.scalar_one_or_none()
                    
                    if credit:
                        credit.balance += credits_to_refund
                        # Create refund transaction
                        refund_txn = CreditTransaction(
                            organisation_id=job.org_id,
                            amount=credits_to_refund,
                            type=TransactionType.REFUND,
                            job_id=job.id,
                            description=f"Refund for failed job: {job_id}"
                        )
                        db.add(refund_txn)
                        print(f"Refunded {credits_to_refund} credits for job {job_id}")
                
                await db.commit()
                raise  # Final failure - don't retry
            else:
                job.status = JobStatus.PENDING
                job.error_message = error_message
                print(f"Job {job_id} will retry in 5 seconds...")
                await db.commit()
                # Use ARQ's Retry with 5-second delay
                raise Retry(defer=5)


async def process_analyze_job(ctx: dict, job_id: str) -> dict:
    """Process an analyze job using Gemini."""
    print(f"Processing analyze job: {job_id}")
    
    async with AsyncSessionLocal() as db:
        stmt = select(Job).where(Job.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return {"status": "error", "message": "Job not found"}
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.attempt_count += 1
        await db.commit()
        
        try:
            input_data = json.loads(job.input_data)
            text = input_data.get("text", "")
            
            if not text:
                raise ValueError("No text provided")
            
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(f"Analyze this: {text}")
            analysis = response.text
            
            job.status = JobStatus.COMPLETED
            job.output_data = json.dumps({"analysis": analysis})
            job.completed_at = datetime.utcnow()
            await db.commit()
            
            return {"status": "completed", "analysis": analysis}
        except Exception as e:
            error_message = str(e)
            print(f"Job {job_id} failed: {error_message}")
            
            if job.attempt_count >= 3:
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.completed_at = datetime.utcnow()
            else:
                job.status = JobStatus.PENDING
                job.error_message = error_message
            
            await db.commit()
            return {"status": "failed", "error": error_message}


# Register functions for ARQ
ARQ_FUNCTIONS = [
    process_summarize_job,
    process_analyze_job,
]


async def enqueue_job(job_type: str, job_id: str) -> bool:
    """Enqueue a job for background processing using ARQ."""
    from arq import create_pool
    
    try:
        # Create ARQ Redis pool using from_dsn
        redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        
        # Enqueue the job using ARQ's native method
        await redis.enqueue_job(f"process_{job_type}_job", job_id)
        
        print(f"Enqueued {job_type} job: {job_id}")
        
        await redis.close()
        return True
    except Exception as e:
        print(f"Failed to enqueue job: {e}")
        return False


async def main():
    """Run the worker using arq cli."""
    print("Use: arq app.worker.WorkerSettings")
    print(f"Redis: {settings.REDIS_URL}")


class WorkerSettings:
    """Settings for ARQ worker - use with 'arq app.worker.WorkerSettings'"""
    redis_settings = RedisSettings(host="localhost", port=6379)
    job_timeout = 300
    max_tries = 3
    functions = ARQ_FUNCTIONS


if __name__ == "__main__":
    asyncio.run(main())
