from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from datetime import datetime, timezone
import uuid
from app.db.base import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    alert_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.transaction_id"))
    alert_reason = Column(String)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

