"""
Prometheus metrics endpoint.

Exposes system metrics for monitoring.
"""
from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

# ============================================
# HTTP Request Metrics
# ============================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ============================================
# Business Metrics - Credits
# ============================================

credits_deducted = Counter(
    'credits_deducted_total',
    'Total credits deducted',
    ['org_id', 'job_type']
)

credits_refunded = Counter(
    'credits_refunded_total',
    'Total credits refunded',
    ['org_id', 'job_type']
)

org_credit_balance = Gauge(
    'org_credit_balance',
    'Current credit balance per organisation',
    ['org_id']
)

# ============================================
# Business Metrics - Jobs
# ============================================

jobs_queued = Counter(
    'jobs_queued_total',
    'Total jobs queued',
    ['org_id', 'job_type']
)

jobs_completed = Counter(
    'jobs_completed_total',
    'Total jobs completed successfully',
    ['org_id', 'job_type']
)

jobs_failed = Counter(
    'jobs_failed_total',
    'Total jobs failed',
    ['org_id', 'job_type']
)

jobs_retry_total = Counter(
    'jobs_retry_total',
    'Total job retry attempts',
    ['org_id', 'job_type']
)

# ============================================
# Queue Metrics
# ============================================

job_queue_depth = Gauge(
    'job_queue_pending_count',
    'Current number of pending/running jobs',
    ['org_id']
)

# ============================================
# Rate Limiting Metrics
# ============================================

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total requests blocked by rate limiting',
    ['org_id']
)

# ============================================
# Webhook Metrics
# ============================================

webhooks_sent = Counter(
    'webhooks_sent_total',
    'Total webhooks sent',
    ['org_id', 'status']
)

webhooks_failed = Counter(
    'webhooks_failed_total',
    'Total webhooks failed',
    ['org_id']
)


# ============================================
# Metrics Helper Functions
# ============================================

def track_request(method: str, endpoint: str, status: int, duration_seconds: float):
    """
    Record HTTP request metrics.
    
    Call this after each request.
    """
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()
    
    http_request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration_seconds)


def track_credit_deduction(org_id: str, job_type: str, amount: int):
    """Record credits deducted for a job."""
    credits_deducted.labels(
        org_id=org_id,
        job_type=job_type
    ).inc(amount)


def track_credit_refund(org_id: str, job_type: str, amount: int):
    """Record credits refunded for a failed job."""
    credits_refunded.labels(
        org_id=org_id,
        job_type=job_type
    ).inc(amount)


def update_credit_balance(org_id: str, balance: int):
    """Update current credit balance gauge."""
    org_credit_balance.labels(org_id=org_id).set(balance)


def track_job_queued(org_id: str, job_type: str):
    """Record a job being queued."""
    jobs_queued.labels(org_id=org_id, job_type=job_type).inc()


def track_job_completed(org_id: str, job_type: str):
    """Record a job completing successfully."""
    jobs_completed.labels(org_id=org_id, job_type=job_type).inc()


def track_job_failed(org_id: str, job_type: str):
    """Record a job failing."""
    jobs_failed.labels(org_id=org_id, job_type=job_type).inc()


def track_job_retry(org_id: str, job_type: str):
    """Record a job retry attempt."""
    jobs_retry_total.labels(org_id=org_id, job_type=job_type).inc()


def update_queue_depth(org_id: str, depth: int):
    """Update pending job count."""
    job_queue_depth.labels(org_id=org_id).set(depth)


def track_rate_limit_exceeded(org_id: str):
    """Record a rate limit block."""
    rate_limit_exceeded.labels(org_id=org_id).inc()


def track_webhook_sent(org_id: str, status: str):
    """Record a webhook being sent."""
    webhooks_sent.labels(org_id=org_id, status=status).inc()


def track_webhook_failed(org_id: str):
    """Record a webhook failure."""
    webhooks_failed.labels(org_id=org_id).inc()


# ============================================
# Prometheus Endpoint
# ============================================

@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns all registered metrics in Prometheus format.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
