# Task 4 Specification: Credit Deduction Safety

## One-Paragraph Specification

**Rule:** When a job is created, deduct credits from the organisation's balance immediately. If the job completes successfully, the deducted credits are consumed. If the job fails permanently after all 3 retry attempts, the credits must be refunded to the organisation's balance.

**Reason:** This ensures users only pay for successfully completed work. Since AI API calls cost money, we must deduct credits upfront to prevent abuse, but must refund if the service fails to deliver results.

**Edge Cases:**
1. Job succeeds after retries - credits already deducted, no further action needed
2. Job fails permanently - must refund exactly the amount deducted
3. Insufficient credits - job creation should fail before deducting
4. Race conditions - credit operations must be atomic using database transactions
5. Duplicate refunds - check if refund already exists for job_id before processing

---

## Demo Gate Requirements

- Start with 100 credits
- Trigger a job that will fail
- Watch credits deduct to 90
- Watch job fail after 3 retries
- Watch credits refund to 100
- Two CreditTransactions rows visible: deduction and refund, both referencing the same job_id

---

## Implementation

### Job Creation (routes/jobs.py):
- Check sufficient credits exist
- Deduct credits atomically
- Create CreditTransaction (DEDUCTION)

### Job Failure (worker.py):
- On permanent failure, refund credits
- Create CreditTransaction (REFUND) with same job_id
