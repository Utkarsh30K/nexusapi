"""
Structured logging configuration using structlog.

All logs are output as JSON with consistent context fields.
"""
import structlog
import logging
import sys
import os


def configure_logging():
    """Configure structlog for JSON output with context."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


# Create logger instance
logger = configure_logging()


def get_logger(**context):
    """
    Get a logger with additional context bound.
    
    Usage:
        log = get_logger(org_id=org_id, user_id=user_id)
        log.info("message", extra_field=value)
    """
    return logger.bind(**context)
