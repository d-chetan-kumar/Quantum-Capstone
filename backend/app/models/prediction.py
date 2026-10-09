from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
import uuid
from datetime import datetime, timezone
from app.db.base import Base

class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    prediction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.transaction_id"))
    
    # ML Details
    model_name = Column(String)
    model_version = Column(String)
    
    # Classical AI
    fraud_probability = Column(Float)
    predicted_class = Column(Integer)
    
    # Kept for future phases
    quantum_probability = Column(Float, nullable=True)
    hybrid_probability = Column(Float, nullable=True)
    final_risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    
    execution_time_ms = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

