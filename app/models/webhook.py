"""
Webhook Delivery Model

Tracks outbound webhook deliveries.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.models.base import Base


class WebhookDelivery(Base):
    """Webhook delivery tracking."""
    __tablename__ = "webhook_deliveries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organisation_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    url = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, delivered, failed
    attempts = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    response_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
