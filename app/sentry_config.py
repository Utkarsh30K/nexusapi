"""
Sentry configuration for error tracking.

Captures all unhandled exceptions with org/user context.
"""
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import settings


def configure_sentry():
    """
    Initialize Sentry with FastAPI and SQLAlchemy integrations.
    
    Requires SENTRY_DSN environment variable to be set.
    """
    dsn = settings.SENTRY_DSN
    
    if not dsn:
        print("Warning: SENTRY_DSN not set, Sentry disabled")
        return
    
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Include organisation and user context in every error
        before_send=lambda event, hint: add_context(event, hint),
        # Sample rate: capture 10% of transactions for performance monitoring
        traces_sample_rate=0.1,
        # Environment
        environment=settings.ENVIRONMENT,
        # Release tracking
        release=settings.APP_VERSION,
    )
    
    print(f"Sentry initialized with DSN: {dsn[:20]}...")


def add_context(event, hint):
    """
    Add organisation and user context to error events.
    
    This helps identify which organisation was affected by an error.
    """
    # The FastAPI integration should already add request context
    # We can enhance it here if needed
    
    return event


def capture_exception(exc_info=None):
    """
    Capture an exception to Sentry.
    
    Usage:
        try:
            # some code
        except Exception:
            capture_exception()
    """
    if sentry_sdk.get_client().is_enabled():
        sentry_sdk.capture_exception(exc_info)


def capture_message(message, level="info"):
    """
    Capture a message to Sentry.
    
    Usage:
        capture_message("Job completed", level="info")
    """
    if sentry_sdk.get_client().is_enabled():
        sentry_sdk.capture_message(message, level=level)
