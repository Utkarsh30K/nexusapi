# Task 4: JWT with Organisation Context and Role-Based Middleware

## Testing Instructions

The server should auto-reload. Follow these steps to verify the demo gate:

---

## Step 1: Login and Get Token

1. Go to: `http://localhost:8000/auth/login/google`
2. Complete Google OAuth login
3. **Copy the `access_token` from the response**

---

## Step 2: Test Endpoints

### Test 1: Public Endpoint (No Auth Required)

```bash
curl http://localhost:8000/api/public
```

**Expected:** `{"message": "This is a public endpoint"}`

---

### Test 2: Authenticated Endpoint (Valid Token Required)

```bash
curl -H "Authorization: Bearer <YOUR_TOKEN>" http://localhost:8000/api/authenticated
```

**Expected:** Returns user info from JWT (user_id, org_id, role, email)

---

### Test 3: Admin-Only Endpoint (As Admin)

If your user is an admin:

```bash
curl -H "Authorization: Bearer <YOUR_TOKEN>" http://localhost:8000/api/admin-only
```

**Expected:** `{"message": "This is an admin-only endpoint", "admin": {...}}`

---

### Test 4: Admin-Only Endpoint (As Member) - Should Fail

If you have a member user:

```bash
curl -H "Authorization: Bearer <MEMBER_TOKEN>" http://localhost:8000/api/admin-only
```

**Expected:** `{"detail": "Admin access required"}` with 403 status

---

### Test 5: Org Data Endpoint (Org Isolation)

```bash
curl -H "Authorization: Bearer <YOUR_TOKEN>" http://localhost:8000/api/org-data
```

**Expected:** Returns org_id - demonstrating that users can only see their own org's data

---

## Demo Gate Requirements

| Requirement                                  | How to Test                                   |
| -------------------------------------------- | --------------------------------------------- |
| Member cannot call admin-only endpoints      | Login as member, call `/api/admin-only` → 403 |
| Admin can call admin-only endpoints          | Login as admin, call `/api/admin-only` → 200  |
| User from org 1 cannot retrieve org 2's data | Call `/api/org-data` → shows only your org    |

---

## API Endpoints Summary

| Endpoint             | Auth Required | Role Required |
| -------------------- | ------------- | ------------- |
| `/api/public`        | No            | Any           |
| `/api/authenticated` | Yes (JWT)     | Any           |
| `/api/admin-only`    | Yes (JWT)     | Admin only    |
| `/api/org-data`      | Yes (JWT)     | Any           |

---

## Troubleshooting

### 401 Unauthorized

- Make sure you're using the correct token
- Token should start with `eyJ...`

### 403 Forbidden

- You're logged in as a member, not admin
- Try with an admin account (first user from domain)

### Token Not Returned

- Make sure you're logged in via Google OAuth
- Check the response includes `access_token`
