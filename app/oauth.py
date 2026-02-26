"""
Google OAuth 2.0 configuration and client.

SECURITY: This module handles OAuth authentication.
"""
from authlib.integrations.starlette_client import OAuth
from app.config import settings

# Create OAuth registry
oauth = OAuth()

# Register Google OAuth client
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
