

| Engineering Intern Track Backend Engineering · API Integration · Deployment *A structured learning and contribution track for engineering interns* |
| :---- |

# **Overview**

This document describes the engineering intern track used to onboard and develop backend engineering talent. It is structured as a progression of hands-on assignments that build toward real contribution on a production codebase.

Interns are not given tutorials or watch-and-learn exercises. From day one they are building real software — a multi-tenant API platform — using the same stack, the same tools, and the same engineering lifecycle as the production team.

By the end of the track, an intern can read a technical specification document, write code that matches it exactly, submit a pull request in the correct format, and participate in the engineering review cycle. That is the entry point for production contribution.

## **What the intern builds**

One product, built across five assignments. Nothing is thrown away between assignments — every table, every service, and every pattern compounds. The product is called NexusAPI: a multi-tenant backend platform where organisations sign up, manage users, purchase credits, and call AI-powered endpoints. By the final assignment it has a Next.js frontend, a background job system, full observability, and automated deployment to the cloud.

## **Stack**

* Backend: Python 3.12, FastAPI, SQLAlchemy (async)

* Database: PostgreSQL with Alembic migrations

* Queue: Redis \+ ARQ for background job processing

* Auth: Google OAuth 2.0 \+ JWT

* Payments: Stripe Checkout \+ Webhooks

* Frontend: Next.js 14 with NextAuth.js

* Observability: structlog, Sentry, Prometheus

* CI/CD: GitHub Actions \+ Google Cloud Build \+ Cloud Run

* AI tool: Gemini (used as a coding partner throughout)

## **Progression model**

The track has three phases of Kasparro contribution that an intern moves through over time.

* Phase 1 — Utility contributor. Closes well-scoped pull requests where deep domain knowledge is not required. Bug fixes, logging improvements, test coverage, small utility functions.

* Phase 2 — Module contributor. Owns a full module within a pillar under senior engineer supervision. Reads the full specification pack, builds to spec, escalates blockers in writing before deviating.

* Phase 3 — Independent module owner. Owns a module end to end. Writes pull requests, handles review feedback, flags specification conflicts upstream.

This track prepares an intern for Phase 1 contribution by the end, with the foundations to move into Phase 2 within their first quarter on the team.

## **Assignment summary**

| Assignment | Core Focus | Key Skills | Demo Gate |
| :---- | :---- | :---- | :---- |
| 1 | Secure multi-tenant foundation | FastAPI, PostgreSQL, Alembic, Google OAuth, JWT, role-based access | Two organisations, strict data isolation, protected routes working |
| 2 | Async job queue \+ background processing | ARQ, Redis, background workers, retry logic, credit safety | Jobs queued, processed async, retried on failure, credits refunded correctly |
| 3 | Production patterns \+ Kasparro lifecycle | Redis caching, rate limiting, API versioning, webhooks, spec → PR cycle | Every feature shipped via mini spec \+ PR in Engineer Bridge Protocol format |
| 4 | Next.js frontend integration | Next.js 14, NextAuth, API binding, error states, loading states, debugging | Auth flow, credit dashboard, job polling UI — all error states handled |
| 5 | Production hardening \+ first real spec closure | Observability, security audit, CI/CD, reading a real build spec | Live on Cloud Run, auto-deploys on merge, first founder-reviewed PR closed |

| Assignment 1 — Secure Multi-Tenant Foundation |
| :---- |

## **What is being built**

A FastAPI backend with PostgreSQL, structured configuration, proper logging, Google OAuth login, JWT authentication, and a multi-tenancy data model. Every subsequent assignment inherits this foundation.

## **What makes this hard**

Multi-tenancy. In a basic backend there is one user pool. Here, every user belongs to an organisation. An organisation has its own credit balance, its own members, and its own usage history. One user cannot see another organisation’s data — ever. This is enforced at the database query level, not just in application logic. Getting this wrong in production causes data leakage between customers.

| Analogy | *Multi-tenancy is like an apartment building. The building is one system. Each apartment is a tenant. Residents belong to one apartment. The building manager makes sure of that — the lock is on the key itself, not just on the door.* |
| :---: | :---- |

## **Tasks**

### **Task 1 — Project scaffold and database schema**

Set up the project with a clean folder structure: routes, models, services, config, migrations. Create four tables with correct foreign keys and indexes: Organisations, Users (with organisation\_id and role), OrgCredits, and CreditTransactions. Every query that touches user data must include organisation\_id as a filter. This rule is documented in a comment at the top of every service file.

**Demo gate:**

Four tables exist with correct relationships. A script creates two organisations and two users in different orgs. A query for org 1’s users cannot return org 2’s users under any condition.

### **Task 2 — Database migrations with Alembic**

In a basic project, tables are created by running Python scripts directly. That approach fails the moment there is real data — you cannot delete and recreate tables in production. Alembic tracks what the database looks like now and generates migration scripts that move it forward without destroying existing data. The intern sets up Alembic, generates an initial migration, runs it, then adds a column and generates a second migration to prove the system works incrementally.

**Demo gate:**

alembic history shows two migration versions. The Users table has the new column. Existing rows were not deleted.

### **Task 3 — Google OAuth with organisation auto-creation**

When a user signs in with Google for the first time, the system checks their email domain. If no organisation exists for that domain, it creates one and makes the user an admin. If an organisation already exists, the user joins as a member. This is a standard SaaS onboarding pattern.

**Demo gate:**

A new Google account signs in. An organisation is created automatically. A second account with the same domain joins the same organisation, not a new one.

### **Task 4 — JWT with organisation context and role-based middleware**

The JWT token contains user id, organisation\_id, and role (admin or member). Two middleware dependencies are written: require\_auth (any valid token) and require\_admin (valid token plus admin role). Three test endpoints demonstrate all access control cases.

**Demo gate:**

A member cannot call admin-only endpoints. An admin can. A user from org 1 cannot retrieve org 2’s data even with a valid token.

| Assignment 2 — Async Job Queue \+ Background Processing |
| :---- |

## **What is being built**

A background job system where long-running tasks are queued and processed asynchronously. The API returns a job ID immediately. The client polls for results. This is the same pattern used in the production audit pipeline.

## **What makes this hard**

In a basic backend, an AI call blocks the HTTP request until it finishes. That breaks at scale and with slow AI responses. Real systems queue the work, return instantly, and let the client check back. The intern must also handle credit safety: if a job fails permanently after all retries, the credits must be refunded — and that refund logic must be atomic so a partial failure cannot leave the user in an inconsistent state.

| Analogy | *It’s like ordering food at a restaurant. You don’t stand at the kitchen window watching your food cook. You get a table number (job ID) and sit down. The kitchen processes jobs independently of the dining room.* |
| :---: | :---- |

## **Tasks**

### **Task 1 — Job table and status model**

A Jobs table is created with: id, org\_id, user\_id, job\_type, status (pending / running / completed / failed), input\_data, output\_data, error\_message, and timestamps for each status transition. Four service functions are written: create\_job, claim\_job, complete\_job, fail\_job. These are the only four ways job status changes.

**Demo gate:**

Five jobs created, claimed, completed, and failed via a test script. Every row shows correct status and timestamps.

### **Task 2 — Background worker with ARQ**

ARQ (a Python async task queue backed by Redis) is set up as the worker. The first background task reads a job’s input from the database, calls Gemini, writes the result back, and marks the job completed or failed. The POST /api/summarize endpoint is rewritten to enqueue the job and return a job\_id immediately — under 100ms — without waiting for Gemini.

**Demo gate:**

POST /api/summarize returns a job\_id in under 100ms. Polling GET /jobs/{job\_id} shows status: pending, then status: completed with Gemini output. The Jobs table shows both started\_at and completed\_at populated.

### **Task 3 — Retry logic for failed jobs**

If a job fails, it retries up to 3 times with a 5-second delay between attempts. After 3 failures the job is marked permanently failed and the error is logged.

**Demo gate:**

A job goes through 3 retry attempts visible in the logs with timestamps 5 seconds apart. Final status is failed with attempt\_count: 3\.

### **Task 4 — Credit deduction safety**

Credits are deducted when a job is created. If the job fails permanently after all retries, credits are refunded. The intern writes a one-paragraph specification document stating the rule, the reason, and the edge cases before writing any code. Code follows the document, not the other way around.

**Demo gate:**

Start with 100 credits. Trigger a job that will fail. Watch credits deduct to 90\. Watch job fail after 3 retries. Watch credits refund to 100\. Two CreditTransactions rows visible: deduction and refund, both referencing the same job\_id.

| Assignment 3 — Production Patterns \+ Kasparro Engineering Lifecycle |
| :---- |

## **What changes in this assignment**

Every feature from this point forward ships through the engineering lifecycle used on the production codebase. Before writing any code, the intern writes a mini build specification for the feature. They build it. They submit a pull request in the correct format. The reviewer evaluates intent versus implementation — not code syntax.

This is not additional process. This is how real engineering on the team works. The goal is to build the habit before touching the actual codebase.

## **The mini build spec format**

* What this feature does (one paragraph)

* What it does not do (one paragraph — scope boundary)

* Exact inputs, outputs, and failure modes for every function planned

If the intern cannot write this before coding, they are not ready to code it.

## **The PR format**

* What changed

* What specification requirement it addresses

* Any deviations from the mini spec and why

* What breaks if this PR is reverted

## **Tasks**

### **Task 1 — Redis caching (first spec → PR cycle)**

Cache Gemini responses for identical inputs for 1 hour. If the same text is summarised twice, the second request hits the cache, costs zero credits, and returns in under 50ms. The cache key is the SHA-256 hash of job type plus input text. If the cache is unavailable, the system falls back to Gemini without crashing — cache down is not an outage.

**Demo gate:**

Same text called twice. First call: Gemini fires, takes 2–3 seconds, costs 10 credits. Second call: cache hit, returns in under 50ms, costs 0 credits. Redis killed: third call falls back to Gemini without crashing.

### **Task 2 — Rate limiting with Redis (spec → PR)**

Per-organisation rate limit of 100 requests per 15 minutes across all endpoints. Not per-user — per organisation. If an org has 10 users all calling the API simultaneously, they share one rate limit bucket. Implemented using Redis sorted sets (the correct data structure for sliding window rate limiting).

**Demo gate:**

A script fires 110 requests from the same org in under a minute. Exactly 100 succeed. 10 return 429 with a retry\_after header.

### **Task 3 — API versioning (spec → PR)**

All current routes move to /v1/. A /v2/summarize endpoint is created with an additional response field. The /v1/ endpoint continues to work and returns the original response shape with no breaking changes. The spec written before building must include: how new versions are added, what constitutes a breaking change, and what the deprecation policy is.

**Demo gate:**

/v1/summarize and /v2/summarize both work simultaneously with different response shapes. A client using v1 is completely unaffected by v2.

### **Task 4 — Outbound webhook delivery (spec → PR)**

Organisations register a webhook URL. When a job completes or fails, the system POSTs the result to that URL. If the POST fails it retries 3 times with exponential backoff: 5 seconds, 25 seconds, 125 seconds. Every outbound webhook is signed with HMAC-SHA256 using the organisation’s secret so the receiver can verify authenticity. This is the same signing pattern used by Stripe.

**Demo gate:**

A webhook URL is registered using webhook.site. A job triggers. The webhook arrives with the correct signature header. A broken URL is registered and the retry attempts appear in the WebhookDeliveries table with timestamps matching the backoff intervals.

| Assignment 4 — Next.js Frontend Integration |
| :---- |

## **What is being built**

A Next.js frontend that connects to the NexusAPI backend. Not a design project. A functional integration with real authentication, real API calls, real error handling, and real loading states. The central skill is: what happens when the backend returns an error — does the frontend break, freeze, or tell the user something useful?

| Analogy | *Frontend-backend integration is like a telephone operator. The frontend doesn’t talk to the database directly — it talks to the backend through defined endpoints. The operator needs to know what to do when the line is busy (loading), when the call drops (error), and when it connects (success). All three must be handled.* |
| :---: | :---- |

## **Tasks**

### **Task 1 — Next.js setup \+ Google OAuth flow**

Next.js 14 is set up with the App Router. Google OAuth is implemented using NextAuth.js. On successful login, the backend JWT is stored in an httpOnly cookie — not localStorage. Auth tokens must never be accessible to client-side JavaScript.

**Demo gate:**

User signs in with Google. JWT is in an httpOnly cookie. Browser dev tools confirm it is not accessible to JavaScript.

### **Task 2 — Credit dashboard with real-time polling**

A dashboard shows: organisation name, current credit balance, last 10 transactions, and a bar chart of credits spent per day for the last 7 days. The balance polls every 30 seconds. A custom React hook useCredits() handles polling, loading state, and error state. If the API call fails, the dashboard shows the last known balance with a timestamp — it does not crash or show a blank screen.

**Demo gate:**

An API call is triggered via the terminal. Within 30 seconds the dashboard credit balance updates automatically. The FastAPI server is stopped. The dashboard gracefully shows last known balance without crashing.

### **Task 3 — API call UI with job polling**

A two-panel interface: left panel has a textarea and two buttons (Summarise — 10 credits; Analyse — 25 credits). Right panel shows the job result. When a button is clicked, the UI goes into a loading state, a job is created, the frontend polls for completion every 2 seconds, and the result appears without a page refresh. Failed jobs show the error message. Network failures show a human-readable error — not a JavaScript stack trace.

**Demo gate:**

A request is submitted. Loading spinner appears. Result appears without page refresh. Internet is disconnected mid-request. Frontend handles it with a readable error message.

### **Task 4 — Debugging exercise**

Three bugs are deliberately introduced into the frontend-backend integration and fixed. For each bug the intern writes: what the symptom was, where they found it (network tab, console, backend logs), what the root cause was, and what the fix was. This document is submitted with the PR.

* Bug 1: Auth token sent in the wrong header format — backend returns 401, frontend shows a blank page instead of redirecting to login

* Bug 2: Credit balance returned as a string instead of a number — chart breaks silently with no visible error

* Bug 3: Job polling does not stop when the job completes — keeps polling indefinitely, hammering the backend

**Demo gate:**

All three bugs demonstrated in a screen share — broken behaviour and fix shown for each one.

| Assignment 5 — Production Hardening \+ First Real Spec Closure |
| :---- |

## **What is being built**

The system becomes production-honest. Full observability, security hardening, automated CI/CD, and the intern’s first experience reading and closing against a real specification document written in the format used by the production team.

## **Tasks**

### **Task 1 — Full observability stack**

Three things are set up. Structured JSON logging with structlog: every log line is machine-readable with org\_id, user\_id, job\_id, route, duration\_ms, and status. Sentry for error tracking: all unhandled exceptions captured with full organisation and user context. Prometheus metrics: requests per second, p50/p95/p99 response times, error rate, and job queue depth, all exposed on GET /metrics.

The intern also writes a runbook: a plain-English document explaining what each metric means, what a healthy value looks like, and what to do if it goes out of range. One paragraph per metric. This is the document an on-call engineer reads at 2am.

**Demo gate:**

Three different errors deliberately triggered. All three appear in Sentry within seconds with correct org context. /metrics shows request counts and error rates populated. Intern walks through the runbook verbally.

### **Task 2 — Security audit**

A security checklist is written before any code changes are made. Every endpoint is audited against it.

* Is organisation\_id enforced at the query level (not just the logic level)?

* Is every input validated before it touches the database?

* Do error responses expose any internal details (stack traces, table names, query strings)?

* Are all secrets in environment variables with no exceptions?

* Are outbound webhook signatures verified?

* Is the JWT expiry set correctly and justified?

For every no answer found, the issue is fixed and documented in the PR.

**Demo gate:**

Checklist presented with every item checked. Three items shown with before (vulnerable) and after (fixed) state.

### **Task 3 — GitHub Actions CI \+ Cloud Build CD**

The CI pipeline runs three checks before any PR can merge: a health check test, a database migration check (runs alembic upgrade head against a test database, fails if migrations are broken), and a security lint check using bandit (catches hardcoded secrets and common vulnerability patterns). The CD pipeline deploys to Cloud Run with all environment variables sourced from Google Secret Manager — no secrets in any config file.

**Demo gate:**

A PR is created with a deliberate migration conflict. CI fails on the migration check. The conflict is fixed. CI passes. Code is merged. Cloud Build deploys automatically. The live Cloud Run URL is shown serving the application.

### **Task 4 — First real specification closure**

This is the most important task in the entire track.

A two-page specification document is written by the reviewer in the format used by the production team. It covers a concrete feature with a defined input, output, and JSON response shape. The specification contains one intentional ambiguity that requires escalation before building.

The intern reads the spec. They write their questions in writing before touching any code. Questions are answered. They write their own mini build spec for the feature. They build it. They submit a PR in the correct format. The reviewer reviews it as a real PR: intent versus implementation. The intern responds to review notes. A second commit addresses the feedback. The PR is merged.

**Demo gate:**

A working, merged PR. Review notes on record. Intern response to those notes. This is not a training exercise — this is the engineering lifecycle, run for real.

| What an Intern Can Do After This Track |
| :---- |

## **Engineering capabilities**

* Build and deploy a production-shaped backend system from scratch

* Design and enforce multi-tenant data isolation at the database level

* Implement async background job processing with retry and failure handling

* Integrate third-party services (OAuth, Stripe, Gemini) with correct error handling and security

* Build a Next.js frontend that connects to a real backend API and handles all failure states

* Set up structured observability: logging, error tracking, and metrics

* Write and run database migrations safely on live data

* Configure CI/CD pipelines that enforce quality gates before deployment

## **Engineering process capabilities**

* Read a technical specification document and identify what is being asked, what is out of scope, and what needs clarification

* Write a mini build spec before coding any feature

* Escalate in writing when a specification requirement is technically impossible — before building a workaround

* Submit pull requests in the correct format: what changed, what spec requirement it addresses, what breaks if reverted

* Respond to review feedback with a second commit, not a verbal explanation

* Treat a schema change as a versioning event, not an edit

## **What they are not yet ready for**

Deep domain contribution. The track builds engineering habits and system-level thinking. Domain-specific knowledge — the business logic, the scoring models, the audit methodology — is acquired separately through reading module specifications and working alongside senior engineers on scoped tasks. That is Phase 2 and Phase 3 of contribution, which begin after this track is complete.

| Appendix — Engineering Principles Applied Throughout |
| :---- |

## **On using AI as a coding tool**

Interns use Gemini as a coding partner throughout the track. The skill being built is not typing less — it is directing precisely and verifying ruthlessly. Gemini produces output at speed. The engineer decides whether that output is correct, safe, and aligned with the specification. Accepting code without understanding it is treated as an error, not a shortcut.

The central discipline: after Gemini writes something, every line is read before it is run. Lines that are not understood are questioned before proceeding. This habit is established in the first week and maintained throughout.

## **On specification compliance**

From Assignment 3 onward, all features are built against a written specification. The rule is simple: if the specification and the code conflict, the code is wrong — not the specification. If a specification requirement is technically impossible, the engineer escalates in writing before building a workaround. Silent deviation is a process violation.

## **On failure modes**

Every feature is designed for what happens when things go wrong, not just when they work. A feature that handles the happy path but crashes on bad input is not complete. A cache that takes down the system when Redis is unavailable is a design error. The track reinforces this by requiring failure mode handling in every task and demo gate.

## **On fail-closed behaviour**

Systems halt with a structured error response when they cannot run cleanly. They do not emit partial results, incorrect scores, or misleading outputs. A job that cannot complete is failed and the error is logged. A webhook that cannot be verified is rejected. An API call with invalid input is returned with a specific, actionable error — not a generic 500\. This behaviour is enforced throughout the track and is the expected default on any production system.