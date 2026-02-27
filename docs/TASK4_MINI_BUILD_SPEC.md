# Mini Build Spec: Health Check Endpoint

---

## What This Feature Does

Creates a `/health` endpoint that checks database and Redis connectivity and returns a status JSON indicating overall system health.

---

## What This Feature Does NOT Do

- Does not require authentication
- Does not check other services (Gemini API, etc.)
- Does not perform deep health checks (just connectivity)

---

## Input

- No input parameters (GET request)

---

## Output

### Success (both connected)
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Degraded (one down)
```json
{
  "status": "degraded",
  "database": "connected",
  "redis": "disconnected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Unhealthy (both down)
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "redis": "disconnected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Functions to Create

### 1. check_database_health()
- Input: None
- Output: "connected" or "disconnected"
- Logic: Try to execute "SELECT 1" via SQLAlchemy

### 2. check_redis_health()
- Input: None  
- Output: "connected" or "disconnected"
- Logic: Try to ping Redis

### 3. health_endpoint()
- Input: Request
- Output: JSON response with status
- Logic: Call both check functions, determine overall status

---

## Failure Modes

| Failure | Handling |
|---------|----------|
| DB timeout | Return "disconnected" |
| Redis timeout | Return "disconnected" |
| Exception | Log error, return "disconnected" |

---

## Acceptance Criteria

- [ ] GET /health returns 200
- [ ] Returns "healthy" when both connected
- [ ] Returns "degraded" when one disconnected  
- [ ] Returns "unhealthy" when both disconnected
- [ ] No authentication required
- [ ] Response time under 100ms
