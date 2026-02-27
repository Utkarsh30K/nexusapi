# Observability Runbook

This document explains each metric in the NexusAPI system, what healthy values look like, and what actions to take when things go wrong.

---

## HTTP Metrics

### http_request_duration_seconds

**Description:** Time taken to process HTTP requests, measured in seconds.

**Labels:**
- `method`: HTTP method (GET, POST, etc.)
- `endpoint`: API endpoint path

**Healthy Values:**
- p50 < 50ms
- p95 < 200ms  
- p99 < 500ms

**Alert Thresholds:**
- p95 > 500ms for 5 minutes → Warning
- p95 > 1s for 5 minutes → Critical

**Actions:**
1. Check slow endpoints in logs (filter by endpoint label)
2. Look for database query slowdowns
3. Check if external APIs (Gemini) are slow
4. Consider adding caching for frequently accessed data

---

### http_requests_total

**Description:** Total count of HTTP requests processed.

**Labels:**
- `method`: HTTP method
- `endpoint`: API endpoint
- `status`: HTTP status code (200, 400, 401, etc.)

**Healthy Values:**
- Error rate (4xx + 5xx) < 1% of total requests
- No sudden spikes in request volume

**Alert Thresholds:**
- Error rate > 5% → Warning
- Error rate > 10% → Critical

**Actions:**
1. Check Sentry for error spikes
2. Look at specific status codes:
   - 401: Token expired or invalid → check auth flow
   - 429: Rate limited → check if legitimate traffic spike
   - 500: Server error → check logs immediately

---

## Credit Metrics

### credits_deducted_total

**Description:** Total credits deducted from organisations for jobs.

**Labels:**
- `org_id`: Organisation ID
- `job_type`: Type of job (SUMMARIZE, ANALYZE)

**Healthy Values:**
- Consistent with expected usage patterns
- No unexpected spikes

**Alert Thresholds:**
- Sudden spike in deductions → Check for abuse

---

### credits_refunded_total

**Description:** Total credits refunded for failed jobs.

**Labels:**
- `org_id`: Organisation ID
- `job_type`: Type of job

**Healthy Values:**
- Refund rate < 5% of deductions

**Alert Thresholds:**
- Refund rate > 10% → Warning: Jobs are failing frequently

**Actions:**
1. Check job failure reasons in logs
2. Verify Gemini API is functioning
3. Check for timeout issues

---

### org_credit_balance

**Description:** Current credit balance for each organisation.

**Labels:**
- `org_id`: Organisation ID

**Healthy Values:**
- Positive balances for active organisations

**Alert Thresholds:**
- Any org at 0 credits → Users cannot create jobs

---

## Job Metrics

### jobs_queued_total

**Description:** Total jobs queued for processing.

**Labels:**
- `org_id`: Organisation ID
- `job_type`: Type of job

**Usage:** Track job creation rate

---

### jobs_completed_total

**Description:** Total jobs completed successfully.

**Labels:**
- `org_id`: Organisation ID
- `job_type`: Type of job

**Healthy Values:**
- Completion rate > 90%

---

### jobs_failed_total

**Description:** Total jobs that failed permanently after all retries.

**Labels:**
- `org_id`: Organisation ID
- `job_type`: Type of job

**Healthy Values:**
- Failure rate < 5%

**Alert Thresholds:**
- Failure rate > 10% → Critical

**Actions:**
1. Check job error messages in database
2. Check worker logs for exception traces
3. Verify Gemini API is operational
4. Check Redis connectivity for queue issues

---

### jobs_retry_total

**Description:** Number of job retry attempts.

**Labels:**
- `org_id`: Organisation ID
- `job_type`: Type of job

**Healthy Values:**
- Low retry count relative to jobs_queued

**Alert Thresholds:**
- High retry ratio → System is unstable

---

### job_queue_pending_count

**Description:** Current number of pending/running jobs per organisation.

**Labels:**
- `org_id`: Organisation ID

**Healthy Values:**
- < 50 pending jobs per org

**Alert Thresholds:**
- > 100 pending → Warning
- > 500 pending → Critical

**Actions:**
1. Scale worker instances if running on multiple pods
2. Check Redis connection
3. Check worker process is running
4. Look for deadlocks or slow processing

---

## Rate Limiting

### rate_limit_exceeded_total

**Description:** Total requests blocked by rate limiting.

**Labels:**
- `org_id`: Organisation ID

**Healthy Values:**
- < 10% of total requests

**Alert Thresholds:**
- High rate → Legitimate traffic spike OR attack

**Actions:**
1. Check if org has legitimate high usage
2. Consider increasing rate limit for trusted orgs
3. Investigate if attack pattern

---

## Webhooks

### webhooks_sent_total

**Description:** Total webhooks successfully delivered.

**Labels:**
- `org_id`: Organisation ID
- `status`: HTTP status code from webhook endpoint

---

### webhooks_failed_total

**Description:** Total webhooks that failed after all retries.

**Labels:**
- `org_id`: Organisation ID

**Healthy Values:**
- Failure rate < 5%

**Actions:**
1. Verify webhook URL is correct
2. Check receiving endpoint is operational
3. Review webhook delivery attempts in database

---

## On-Call Checklist

When paged for an alert:

1. **Check the metric** - What exactly is violating the threshold?
2. **Check Sentry** - Are there related errors? Look for patterns
3. **Check logs** - Search for relevant org_id, endpoint, or job_id
4. **Check dependencies** - Is Redis down? Is Gemini API down?
5. **Take action** - Use the specific actions listed above
6. **Document** - Update this runbook if new patterns emerge

---

## Useful Queries

### Find slow requests
```bash
# In logs, filter by duration_ms > 1000
grep '"duration_ms":1' app.log
```

### Check error rate by endpoint
```bash
# Group by endpoint and count 5xx errors
grep '"status_code":5' app.log | jq '.endpoint' -r | sort | uniq -c
```

### Find failing jobs for an org
```bash
# In database
SELECT * FROM jobs WHERE org_id = 'xxx' AND status = 'failed' ORDER BY created_at DESC LIMIT 10;
```
