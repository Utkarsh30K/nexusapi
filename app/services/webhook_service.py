"""
Webhook Service

Handles outbound webhook delivery with retry logic.
"""
import json
import hmac
import hashlib
import asyncio
import httpx
from datetime import datetime, timedelta
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.webhook import WebhookDelivery
from app.models.organisation import Organisation


# Exponential backoff delays: 5s, 25s, 125s
WEBHOOK_DELAYS = [5, 25, 125]
MAX_RETRIES = 3


def generate_webhook_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


async def send_webhook(
    org_id: str,
    job_id: str,
    webhook_url: str,
    payload: dict,
    org_secret: str
) -> bool:
    """
    Send webhook with retry logic.
    
    Returns True if delivered, False otherwise.
    """
    payload_str = json.dumps(payload)
    signature = generate_webhook_signature(payload_str, org_secret)
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Job-Id": job_id
    }
    
    async with AsyncSessionLocal() as db:
        # Create delivery record
        delivery = WebhookDelivery(
            organisation_id=org_id,
            job_id=job_id,
            url=webhook_url,
            status="pending",
            attempts=0
        )
        db.add(delivery)
        await db.commit()
        
        delivery_id = delivery.id
        
        # Try sending with retries
        for attempt in range(MAX_RETRIES):
            delivery.attempts = attempt + 1
            await db.commit()
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook_url,
                        content=payload_str,
                        headers=headers
                    )
                    
                    delivery.response_code = response.status_code
                    
                    if response.status_code >= 200 and response.status_code < 300:
                        delivery.status = "delivered"
                        await db.commit()
                        print(f"Webhook delivered successfully: {webhook_url}")
                        return True
                    else:
                        delivery.error_message = f"HTTP {response.status_code}"
                        
            except Exception as e:
                delivery.error_message = str(e)
                print(f"Webhook attempt {attempt + 1} failed: {e}")
            
            # Schedule next retry or mark as failed
            if attempt < MAX_RETRIES - 1:
                delay = WEBHOOK_DELAYS[attempt]
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
                delivery.status = "pending"
                await db.commit()
                
                # Wait for retry delay
                await asyncio.sleep(delay)
            else:
                delivery.status = "failed"
                await db.commit()
                print(f"Webhook failed after {MAX_RETRIES} attempts: {webhook_url}")
        
        return False


async def trigger_job_webhook(org_id: str, job_id: str, job_result: dict):
    """
    Trigger webhook for job completion/failure.
    Called from worker when job completes.
    """
    # Get organisation webhook URL
    async with AsyncSessionLocal() as db:
        stmt = select(Organisation).where(Organisation.id == org_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        
        if not org or not org.webhook_url:
            print(f"No webhook configured for org {org_id}")
            return
        
        # Send webhook asynchronously (don't block worker)
        asyncio.create_task(
            send_webhook(
                org_id=org_id,
                job_id=job_id,
                webhook_url=org.webhook_url,
                payload=job_result,
                org_secret=org.webhook_secret or ""
            )
        )
