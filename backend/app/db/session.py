import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FALLBACK_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "quantum_fraud.db"))
FALLBACK_DB_URL = f"sqlite:///{FALLBACK_DB_PATH}"

ACTIVE_DB_TYPE = "unknown"
ACTIVE_DB_TARGET = "unknown"
IS_FALLBACK = False

def get_engine():
    global ACTIVE_DB_TYPE, ACTIVE_DB_TARGET, IS_FALLBACK
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("sqlite"):
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
            ACTIVE_DB_TYPE = "sqlite"
            ACTIVE_DB_TARGET = db_url
            IS_FALLBACK = False
        else:
            engine = create_engine(db_url)
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            ACTIVE_DB_TYPE = "postgresql"
            ACTIVE_DB_TARGET = db_url.split("@")[-1] if "@" in db_url else db_url
            IS_FALLBACK = False
            logger.info(f"Connected to primary PostgreSQL database ({ACTIVE_DB_TARGET})")
            return engine
    except Exception as e:
        logger.warning(f"Could not connect to primary database ({db_url}): {e}. Falling back to SQLite at {FALLBACK_DB_PATH}.")
        engine = create_engine(FALLBACK_DB_URL, connect_args={"check_same_thread": False})
        ACTIVE_DB_TYPE = "sqlite_fallback"
        ACTIVE_DB_TARGET = FALLBACK_DB_PATH
        IS_FALLBACK = True
        return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from app.models import Transaction, ModelPrediction, FraudAlert, SimulationRun, ModelEvaluation, SystemEvent
    Base.metadata.create_all(bind=engine)


