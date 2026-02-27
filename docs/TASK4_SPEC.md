# Task 4 Specification: Health Check with Database & Redis Status

---

## Overview

Add a `/health` endpoint to the NexusAPI that provides detailed system health status including database and Redis connectivity checks.

---

## Requirements

### 1. Endpoint

- **Route**: `GET /health`
- **Authentication**: None required (public endpoint)
- **Response Time**: Must respond in under 100ms

### 2. Success Response

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Error Response (Partial Failure)

```json
{
  "status": "degraded",
  "database": "connected",
  "redis": "disconnected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. Error Response (Complete Failure)

```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "redis": "disconnected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Technical Implementation

### Database Check
- Use SQLAlchemy to execute a simple query: `SELECT 1`
- Connection timeout: 3 seconds

### Redis Check
- Use Redis ping command
- Connection timeout: 3 seconds

### Timestamp
- Use UTC timezone
- ISO 8601 format

---

## Edge Cases

1. **Both services down** → Return "unhealthy" status
2. **One service down** → Return "degraded" status  
3. **Timeout** → Treat as "disconnected"
4. **Exception** → Log error, treat as "disconnected"

---

## Acceptance Criteria

| Test Case | Expected Status |
|-----------|-----------------|
| DB connected, Redis connected | healthy |
| DB connected, Redis disconnected | degraded |
| DB disconnected, Redis connected | degraded |
| DB disconnected, Redis disconnected | unhealthy |

---

## File Changes

Create/update:
- `app/routes/health.py` - New route file
- `app/main.py` - Include the router

---

## Verification

Run these tests:
```bash
# Normal case
curl http://localhost:8000/health

# With Redis stopped
# (should show redis: disconnected)
```
