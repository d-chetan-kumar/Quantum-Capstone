from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, Any
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionListResponse
from app.schemas.prediction import PredictionResponse
from app.models.transaction import Transaction
from app.models.prediction import ModelPrediction
from app.db.session import SessionLocal
from app.services.ml_service import ml_service

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TransactionResponse)
def create_transaction(transaction_in: TransactionCreate, db: Session = Depends(get_db)):
    db_obj = Transaction(**transaction_in.model_dump(), status="PENDING")
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=TransactionListResponse)
def read_transactions(skip: int = 0, limit: int = 50, transaction_type: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Transaction)
    if transaction_type: query = query.filter(Transaction.transaction_type == transaction_type)
    if status: query = query.filter(Transaction.status == status)
    
    total = query.count()
    items = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit).all()
    return TransactionListResponse(items=items, total=total, page=(skip // limit) + 1, size=limit)

@router.get("/{transaction_id}", response_model=TransactionResponse)
def read_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx: raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

@router.post("/{transaction_id}/predict", response_model=PredictionResponse)
def predict_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx: raise HTTPException(status_code=404, detail="Transaction not found")
    
    try:
        tx_dict = {
            "amount": tx.amount,
            "type": tx.transaction_type,
            "transaction_type": tx.transaction_type,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
            "step": getattr(tx, "step", None)
        }
        pred_result = ml_service.predict(tx_dict)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    existing = db.query(ModelPrediction).filter(
        ModelPrediction.transaction_id == tx.transaction_id,
        ModelPrediction.model_name == pred_result["model_name"]
    ).first()

    if existing:
        existing.fraud_probability = pred_result["fraud_probability"]
        existing.predicted_class = pred_result["predicted_class"]
        existing.execution_time_ms = pred_result["execution_time_ms"]
        db.commit()
        db.refresh(existing)
        return existing

    pred_obj = ModelPrediction(
        transaction_id=tx.transaction_id,
        model_name=pred_result["model_name"],
        model_version=pred_result["model_version"],
        fraud_probability=pred_result["fraud_probability"],
        predicted_class=pred_result["predicted_class"],
        execution_time_ms=pred_result["execution_time_ms"]
    )
    db.add(pred_obj)
    db.commit()
    db.refresh(pred_obj)
    return pred_obj

@router.get("/{transaction_id}/predict", response_model=PredictionResponse)
def get_prediction(transaction_id: str, db: Session = Depends(get_db)):
    pred = db.query(ModelPrediction).filter(ModelPrediction.transaction_id == transaction_id).order_by(desc(ModelPrediction.created_at)).first()
    if not pred: raise HTTPException(status_code=404, detail="Prediction not found")
    return pred

from app.ml.vqc_service import vqc_service

@router.post("/{transaction_id}/quantum-predict")
def quantum_predict_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx: raise HTTPException(status_code=404, detail="Transaction not found")
    
    if not vqc_service.is_available():
        raise HTTPException(status_code=503, detail="VQC model is not available")
        
    try:
        tx_dict = {
            "amount": tx.amount,
            "type": tx.transaction_type,
            "transaction_type": tx.transaction_type,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
            "step": getattr(tx, "step", None)
        }
        prob, pred_class = vqc_service.predict(tx_dict)
        meta = vqc_service.get_metadata()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Quantum prediction failed: {str(e)}")
        
    existing = db.query(ModelPrediction).filter(
        ModelPrediction.transaction_id == tx.transaction_id,
        ModelPrediction.model_name == "vqc"
    ).first()

    if existing:
        existing.fraud_probability = prob
        existing.quantum_probability = prob
        existing.predicted_class = pred_class
        db.commit()
        db.refresh(existing)
        return {
            "transaction_id": tx.transaction_id,
            "model_name": existing.model_name,
            "model_version": existing.model_version,
            "fraud_probability": prob,
            "predicted_class": pred_class
        }

    pred_obj = ModelPrediction(
        transaction_id=tx.transaction_id,
        model_name="vqc",
        model_version=meta.get("model_version", "v1.0"),
        fraud_probability=prob,
        quantum_probability=prob,
        predicted_class=pred_class,
        execution_time_ms=0.0
    )
    db.add(pred_obj)
    db.commit()
    db.refresh(pred_obj)
    
    return {
        "transaction_id": tx.transaction_id,
        "model_name": pred_obj.model_name,
        "model_version": pred_obj.model_version,
        "fraud_probability": prob,
        "predicted_class": pred_class
    }

from app.services.risk_engine import risk_engine

@router.get("/{transaction_id}/risk")
@router.post("/{transaction_id}/risk")
def calculate_transaction_risk(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    existing_pred = db.query(ModelPrediction).filter(
        ModelPrediction.transaction_id == tx.transaction_id,
        ModelPrediction.hybrid_probability.isnot(None)
    ).order_by(desc(ModelPrediction.created_at)).first()

    if existing_pred and existing_pred.hybrid_probability is not None:
        p_xgb = existing_pred.fraud_probability or 0.0
        p_vqc = existing_pred.quantum_probability if existing_pred.quantum_probability is not None else p_xgb
        p_hybrid = existing_pred.hybrid_probability
        risk_level = existing_pred.risk_level or ("ALERT" if p_hybrid >= 0.70 else ("REVIEW" if p_hybrid >= 0.30 else "SAFE"))
        return {
            "transaction_id": str(tx.transaction_id),
            "classical_probability": p_xgb,
            "quantum_probability": p_vqc,
            "hybrid_probability": p_hybrid,
            "risk_level": risk_level,
            "xgboost_weight": risk_engine.xgb_weight,
            "vqc_weight": risk_engine.vqc_weight,
            "created_at": existing_pred.created_at.isoformat() if existing_pred.created_at else (tx.created_at.isoformat() if tx.created_at else None),
            "model_versions": {"xgboost": "v1.0", "vqc": "v1.0", "hybrid": "v1.0"}
        }

    tx_dict = {
        "amount": tx.amount,
        "type": tx.transaction_type,
        "transaction_type": tx.transaction_type,
        "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
        "step": getattr(tx, "step", None)
    }

    try:
        res = risk_engine.evaluate_transaction(tx_dict, str(tx.transaction_id), db=db)
        
        try:
            pred_obj = ModelPrediction(
                transaction_id=tx.transaction_id,
                model_name="hybrid",
                model_version="v1.0",
                fraud_probability=res["classical_probability"],
                quantum_probability=res["quantum_probability"],
                hybrid_probability=res["hybrid_probability"],
                final_risk_score=res["hybrid_probability"],
                risk_level=res["risk_level"],
                predicted_class=1 if res["risk_level"] == "ALERT" else 0,
                execution_time_ms=0.0
            )
            db.add(pred_obj)
            db.commit()
        except Exception:
            pass

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid risk engine error: {str(e)}")

from app.services.behavioural_risk_service import behavioural_risk_service

@router.get("/{transaction_id}/behaviour")
def get_transaction_behaviour(transaction_id: str, db: Session = Depends(get_db)):
    res = behavioural_risk_service.evaluate_transaction_behaviour(transaction_id, db=db)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res




