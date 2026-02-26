# Google OAuth Setup Guide

## Step-by-Step Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `NexusAPI` or your preferred name
4. Click "Create"

### Step 2: Enable Google+ API or People API

1. In the left sidebar, go to **APIs & Services** → **Library**
2. Search for "Google+ API" or "People API"
3. Click on it and click **Enable**

**Note**: If Google+ API is deprecated, use **People API** instead.

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (for testing)
3. Fill in the required fields:
   - **App name**: NexusAPI
   - **User support email**: your email
   - **Developer contact information**: your email
4. Click **Save and Continue**
5. Skip "Scopes" (no additional scopes needed)
6. Skip "Test users" for now
7. Click **Save and Continue**

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Fill in:
   - **Name**: NexusAPI Web Client
   - **Authorized JavaScript origins**:
     - `http://localhost:8000`
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/google/callback`
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### Step 5: Update Your .env File

Add these to your `.env` file:

```env
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

### Step 6: Run the Application

```bash
# Activate virtual environment
cd nexusapi
venv\Scripts\activate

# Install dependencies (if not already)
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

### Step 7: Test OAuth

1. Open browser to: `http://localhost:8000/auth/login/google`
2. You should be redirected to Google login
3. After login, you'll be redirected back
4. Check the database to see your new user and organisation!

### Step 8: Verify in Database

```bash
# Check organisations
docker exec -it nexusapi_postgres psql -U nexususer -d nexusapi -c "SELECT * FROM organisations;"

# Check users
docker exec -it nexusapi_postgres psql -U nexususer -d nexusapi -c "SELECT * FROM users;"

# Check credits
docker exec -it nexusapi_postgres psql -U nexususer -d nexusapi -c "SELECT * FROM org_credits;"
```

---

## Important Notes

### For Local Development:

- The redirect URI must match exactly: `http://localhost:8000/auth/google/callback`
- OAuth consent screen must have your email as test user (or be verified)

### For Production:

- You need to verify your domain with Google
- Update redirect URIs to your production URL
- Get your app verified by Google

---

## Troubleshooting

### Error: "redirect_uri_mismatch"

- Make sure the redirect URI in Google Console matches exactly: `http://localhost:8000/auth/google/callback`

### Error: "access_denied"

- You need to add your email as a test user in OAuth consent screen
- Or verify your domain with Google

### Error: "invalid_client"

- Check that Client ID and Client Secret are correct in .env file
- Make sure there are no extra spaces or quotes

---

## Demo Gate Requirements

When complete, you should be able to:

1. ✅ Navigate to `/auth/login/google`
2. ✅ Sign in with Google account
3. ✅ See new organisation created (for new domains)
4. ✅ See new user created in database
5. ✅ See credits created for new organisations
