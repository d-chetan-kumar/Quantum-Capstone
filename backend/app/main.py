from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.api.v1 import router as api_v1_router
from app.websocket.stream import router as ws_router
from app.db.session import SessionLocal

from app.db.session import SessionLocal, init_db, ACTIVE_DB_TYPE, ACTIVE_DB_TARGET, IS_FALLBACK

app = FastAPI(title="Quantum Fraud Detection API")

@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws/v1")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass
    
    return {
        "status": "ok", 
        "service": "fraud-detection-backend",
        "database": db_status,
        "database_type": ACTIVE_DB_TYPE,
        "database_target": ACTIVE_DB_TARGET,
        "is_fallback": IS_FALLBACK
    }

@app.get("/api/v1/health/database")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy", 
            "database": "connected",
            "database_type": ACTIVE_DB_TYPE,
            "database_target": ACTIVE_DB_TARGET,
            "is_fallback": IS_FALLBACK,
            "is_postgresql": (ACTIVE_DB_TYPE == "postgresql")
        }
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

