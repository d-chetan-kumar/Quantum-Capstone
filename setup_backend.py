import os
import textwrap

BASE_DIR = r"c:\Users\HP\OneDrive\Desktop\QUANTUM FRAUD DETECTION"

def write_file(path, content):
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# Directories
dirs = [
    "backend/app/api/v1",
    "backend/app/core",
    "backend/app/db",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/websocket",
    "backend/tests",
    "data",
    "models",
    "ml",
    "quantum",
    "scripts",
    "tests",
]
for d in dirs:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

# backend/requirements.txt
write_file("backend/requirements.txt", """
fastapi==0.103.2
uvicorn==0.23.2
sqlalchemy==2.0.21
psycopg2-binary==2.9.9
alembic==1.12.0
pydantic==2.4.2
pydantic-settings==2.0.3
websockets==11.0.3
pytest==7.4.2
""")

# .env.example
write_file(".env.example", """
DATABASE_URL=postgresql://user:password@localhost:5432/quantum_fraud
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:5173
WEBSOCKET_URL=ws://localhost:8000/ws/v1/stream
""")

# docker-compose.yml
write_file("docker-compose.yml", """
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: quantum_fraud
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d quantum_fraud"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: 
      context: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/quantum_fraud
      - FRONTEND_URL=http://localhost:5173
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
      - VITE_WS_BASE_URL=ws://localhost:8000/ws/v1/stream
    depends_on:
      - backend

volumes:
  postgres_data:
""")

# backend/Dockerfile
write_file("backend/Dockerfile", """
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
""")

# frontend/Dockerfile
write_file("frontend/Dockerfile", """
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
""")

# backend/app/main.py
write_file("backend/app/main.py", """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import router as api_v1_router
from app.websocket.stream import router as ws_router

app = FastAPI(title="Quantum Fraud Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws/v1")

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "fraud-detection-backend"}
""")

# backend/app/core/config.py
write_file("backend/app/core/config.py", """
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/quantum_fraud"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
""")

# backend/app/db/session.py
write_file("backend/app/db/session.py", """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
""")

# backend/app/db/base.py
write_file("backend/app/db/base.py", """
from sqlalchemy.orm import declarative_base
Base = declarative_base()
""")

# backend/app/models/all_models.py
write_file("backend/app/models/__init__.py", """
from .transaction import Transaction
from .prediction import ModelPrediction
from .alert import FraudAlert
from .simulation import SimulationRun
from .evaluation import ModelEvaluation
from .event import SystemEvent
""")

# backend/app/models/transaction.py
write_file("backend/app/models/transaction.py", """
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime)
    amount = Column(Float)
    transaction_type = Column(String)
    sender_id = Column(String)
    receiver_id = Column(String)
    location = Column(String)
    status = Column(String)
    created_at = Column(DateTime)
""")

# backend/app/models/prediction.py
write_file("backend/app/models/prediction.py", """
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.transaction_id"))
    classical_probability = Column(Float)
    quantum_probability = Column(Float)
    hybrid_probability = Column(Float)
    final_risk_score = Column(Float)
    risk_level = Column(String)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime)
""")

write_file("backend/app/models/alert.py", """
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.transaction_id"))
    alert_reason = Column(String)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    created_at = Column(DateTime)
""")

write_file("backend/app/models/simulation.py", """
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from app.db.base import Base

class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    simulation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    transactions_generated = Column(Integer)
    configuration = Column(JSON)
""")

write_file("backend/app/models/evaluation.py", """
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from app.db.base import Base

class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"
    evaluation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type = Column(String)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    confusion_matrix = Column(JSON)
    evaluated_at = Column(DateTime)
""")

write_file("backend/app/models/event.py", """
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from app.db.base import Base

class SystemEvent(Base):
    __tablename__ = "system_events"
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime)
""")

write_file("backend/app/api/v1/__init__.py", """
from fastapi import APIRouter
router = APIRouter()
# Empty router for now, will add endpoints in later phases
""")

write_file("backend/app/websocket/stream.py", """
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
router = APIRouter()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # In Phase 1, just echo or handle ping
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
""")

write_file("backend/tests/test_health.py", """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "fraud-detection-backend"}
""")

write_file("README.md", """
# Quantum-Assisted Real-Time Payment Fraud Detection & Authentication Platform

## Architecture
Hybrid classical and quantum AI for real-time payment fraud detection.

## Setup
### Backend
```bash
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up --build
```
""")

print("Backend setup complete.")
