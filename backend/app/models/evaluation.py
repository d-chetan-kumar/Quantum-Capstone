from sqlalchemy import Column, String, Float, DateTime, JSON
import uuid
from app.db.base import Base

class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"
    evaluation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_type = Column(String)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    confusion_matrix = Column(JSON)
    evaluated_at = Column(DateTime)
