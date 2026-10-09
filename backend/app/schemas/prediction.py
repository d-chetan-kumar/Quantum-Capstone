from pydantic import BaseModel, field_serializer
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

class PredictionResponse(BaseModel):
    prediction_id: UUID
    transaction_id: UUID
    model_name: str
    model_version: str
    fraud_probability: float
    predicted_class: int
    execution_time_ms: float
    created_at: datetime

    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime, _info):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    class Config:
        from_attributes = True

