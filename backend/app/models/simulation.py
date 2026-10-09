from sqlalchemy import Column, Integer, DateTime, String, JSON
import uuid
from app.db.base import Base

class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    simulation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    transactions_generated = Column(Integer)
    configuration = Column(JSON)
