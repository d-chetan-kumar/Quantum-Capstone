from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import Optional

from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.services.behavioural_risk_service import behavioural_risk_service

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{account_id}/profile")
def get_account_profile(account_id: str, db: Session = Depends(get_db)):
    profile = behavioural_risk_service.get_account_profile(account_id=account_id, db=db)
    sender_metrics = behavioural_risk_service.compute_sender_behaviour(sender_id=account_id, current_amount=0.0, db=db)
    receiver_metrics = behavioural_risk_service.compute_receiver_behaviour(receiver_id=account_id, db=db)
    
    return {
        **profile,
        "sender_metrics": sender_metrics,
        "receiver_metrics": receiver_metrics
    }

@router.get("/{account_id}/transactions")
def get_account_transactions(account_id: str, limit: int = 20, db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(
        or_(Transaction.sender_id == account_id, Transaction.receiver_id == account_id)
    ).order_by(desc(Transaction.timestamp)).limit(limit).all()
    
    return [
        {
            "transaction_id": str(t.transaction_id),
            "amount": float(t.amount),
            "transaction_type": t.transaction_type,
            "sender_id": t.sender_id,
            "receiver_id": t.receiver_id,
            "status": t.status,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None
        }
        for t in txs
    ]
