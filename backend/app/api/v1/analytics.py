import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.models.alert import FraudAlert
from app.services.ml_service import ml_service
from app.ml.vqc_service import vqc_service
from app.services.risk_engine import risk_engine

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    db_connected = False
    tx_count = 0
    recent_txs = []
    
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        tx_count = db.query(Transaction).count()
        tx_list = db.query(Transaction).order_by(desc(Transaction.timestamp)).limit(10).all()
        recent_txs = [
            {
                "transaction_id": str(t.transaction_id),
                "amount": float(t.amount),
                "transaction_type": t.transaction_type,
                "status": t.status,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None
            }
            for t in tx_list
        ]
    except Exception:
        db_connected = False

    xgb_stat = ml_service.get_status()
    vqc_stat = vqc_service.get_metadata()
    vqc_avail = vqc_service.is_available()
    xgb_avail = (xgb_stat.get("status") == "available")
    hybrid_eval = risk_engine.get_evaluation()

    return {
        "system_status": {
            "backend": "online",
            "database": "connected" if db_connected else "disconnected",
            "xgboost": xgb_stat.get("status", "unavailable"),
            "vqc": "available" if vqc_avail else vqc_stat.get("status", "unavailable"),
            "vqc_diagnostic_reason": vqc_stat.get("diagnostic_reason", ""),
            "hybrid": "available" if (xgb_avail and vqc_avail) else ("degraded" if (xgb_avail or vqc_avail) else "unavailable")
        },
        "transaction_stats": {
            "total_transactions": tx_count,
            "recent_transactions": recent_txs
        },
        "hybrid_evaluation": hybrid_eval
    }

from app.models.prediction import ModelPrediction

@router.get("/performance")
def get_model_performance():
    return risk_engine.get_evaluation() or {}

@router.get("/risk-summary")
def get_risk_summary(db: Session = Depends(get_db)):
    try:
        preds = db.query(ModelPrediction).filter(ModelPrediction.hybrid_probability.isnot(None)).all()
    except Exception:
        preds = []

    total = len(preds)
    safe_count = sum(1 for p in preds if p.risk_level == "SAFE" or (p.hybrid_probability is not None and p.hybrid_probability < 0.30))
    review_count = sum(1 for p in preds if p.risk_level == "REVIEW" or (p.hybrid_probability is not None and 0.30 <= p.hybrid_probability < 0.70))
    alert_count = sum(1 for p in preds if p.risk_level == "ALERT" or (p.hybrid_probability is not None and p.hybrid_probability >= 0.70))

    buckets = {f"{i*10}-{(i+1)*10}%": 0 for i in range(10)}
    for p in preds:
        if p.hybrid_probability is not None:
            score = min(max(p.hybrid_probability, 0.0), 0.9999)
            idx = int(score * 10)
            bucket_key = f"{idx*10}-{(idx+1)*10}%"
            buckets[bucket_key] += 1

    distribution = [{"bucket": k, "count": v} for k, v in buckets.items()]

    return {
        "total_evaluated": total,
        "risk_counts": {
            "SAFE": safe_count,
            "REVIEW": review_count,
            "ALERT": alert_count
        },
        "score_distribution": distribution
    }

