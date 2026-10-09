from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime, timezone
import uuid
from app.db.base import Base

class SystemEvent(Base):
    __tablename__ = "system_events"
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

