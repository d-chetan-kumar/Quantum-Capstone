from sqlalchemy import Column, String, Float, DateTime, Boolean
from datetime import datetime, timezone
import uuid
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_type = Column(String, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sender_id = Column(String, index=True)
    receiver_id = Column(String, index=True)
    location = Column(String, nullable=True)
    status = Column(String, default="PENDING")
    is_simulated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

