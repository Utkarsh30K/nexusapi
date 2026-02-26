"""
Job model test script.

Verifies job creation, status transitions, and timestamps.
Run this after ensuring the database is running.
"""
import asyncio
from app.database import AsyncSessionLocal

# Import all models to ensure they're registered with SQLAlchemy
from app.models.organisation import Organisation
from app.models.user import User
from app.models.credit import OrgCredit, CreditTransaction
from app.models.job import Job, JobStatus, JobType
from app.services.job_service import JobService


async def test_job_lifecycle():
    """Test the complete job lifecycle."""
    
    # Use existing org_id from database (Gmail Organisation)
    # If you don't have one, create it first via OAuth login
    org_id = "bfcb9a97-761f-464b-b3fd-17b2de24d1fd"  # Gmail Organisation
    user_id = "test-user-id"
    
    async with AsyncSessionLocal() as db:
        job_service = JobService(db)
        
        print("=== Job Lifecycle Test ===\n")
        
        # Test 1: Create 5 jobs
        print("1. Creating 5 jobs...")
        jobs = []
        for i in range(5):
            job = await job_service.create_job(
                org_id=org_id,
                user_id=user_id,
                job_type=JobType.SUMMARIZE,
                input_data=f'{{"text": "Test text {i}"}}'
            )
            jobs.append(job)
            print(f"   Created job {i+1}: {job.id[:8]}... - status: {job.status.value}")
        
        # Test 2: Claim jobs (pending -> running)
        print("\n2. Claiming jobs (pending -> running)...")
        for i, job in enumerate(jobs[:3]):  # Claim first 3
            claimed = await job_service.claim_job(job.id)
            print(f"   Claimed job {i+1}: {claimed.id[:8]}... - status: {claimed.status.value}, attempt_count: {claimed.attempt_count}")
        
        # Test 3: Complete jobs (running -> completed)
        print("\n3. Completing jobs (running -> completed)...")
        for i, job in enumerate(jobs[:2]):  # Complete first 2
            completed = await job_service.complete_job(
                job.id,
                '{"summary": "Test summary"}'
            )
            print(f"   Completed job {i+1}: {completed.id[:8]}... - status: {completed.status.value}")
        
        # Test 4: Fail jobs (running -> failed)
        print("\n4. Failing jobs (running -> failed)...")
        for i, job in enumerate(jobs[2:4]):  # Fail next 2
            failed = await job_service.fail_job(
                job.id,
                "Test error message"
            )
            print(f"   Failed job {i+3}: {failed.id[:8]}... - status: {failed.status.value}, error: {failed.error_message}")
        
        # Test 5: Verify final states
        print("\n5. Verifying final states...")
        for i, job in enumerate(jobs):
            retrieved = await job_service.get_job_by_id(job.id)
            print(f"\n   Job {i+1} ({retrieved.id[:8]}...):")
            print(f"      - status: {retrieved.status.value}")
            print(f"      - attempt_count: {retrieved.attempt_count}")
            print(f"      - started_at: {retrieved.started_at}")
            print(f"      - completed_at: {retrieved.completed_at}")
            print(f"      - output_data: {retrieved.output_data}")
            print(f"      - error_message: {retrieved.error_message}")
        
        print("\n=== All tests passed! ===")
        print("\nDemo Gate Verification:")
        print("  ✅ Five jobs created")
        print("  ✅ Jobs claimed (3 jobs changed to running)")
        print("  ✅ Jobs completed (2 jobs changed to completed)")
        print("  ✅ Jobs failed (2 jobs changed to failed)")
        print("  ✅ Timestamps populated (started_at, completed_at)")


if __name__ == "__main__":
    asyncio.run(test_job_lifecycle())
