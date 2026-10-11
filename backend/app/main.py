import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.api.v1 import router as api_v1_router
from app.websocket.stream import router as ws_router
from app.db.session import SessionLocal, init_db, ACTIVE_DB_TYPE, ACTIVE_DB_TARGET, IS_FALLBACK

app = FastAPI(title="Quantum Fraud Detection API")

@app.on_event("startup")
def on_startup():
    init_db()
    # Ensure database has seeded demonstration records on any deployment
    try:
        from app.models.transaction import Transaction
        from app.scripts.seed_paysim_demo import seed_paysim_demo
        db = SessionLocal()
        tx_count = db.query(Transaction).count()
        if tx_count < 100:
            print(f"Deployment auto-seeding: only {tx_count} records found. Seeding demo transactions...")
            seed_paysim_demo(num_sample=200)
        db.close()
    except Exception as e:
        print(f"Startup seeding check note: {e}")

# Permissive CORS regex allowing any localhost, preview, or cloud deployment domain
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws/v1")

# Locate built frontend if available (unified single-service deployment)
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if not os.path.exists(FRONTEND_DIST):
    FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


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

@app.get("/{full_path:path}")
async def serve_spa_route(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("ws/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if os.path.exists(FRONTEND_DIST):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.exists(candidate) and os.path.isfile(candidate):
            return FileResponse(candidate)
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    return JSONResponse(status_code=404, content={"detail": "Frontend bundle not found"})


