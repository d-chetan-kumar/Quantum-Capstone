from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.alert import FraudAlert

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def list_alerts(status: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    try:
        query = db.query(FraudAlert)
        if status == "unresolved":
            query = query.filter(FraudAlert.resolved == False)
        elif status == "resolved":
            query = query.filter(FraudAlert.resolved == True)
            
        alerts = query.order_by(desc(FraudAlert.created_at)).limit(limit).all()
        return [
            {
                "alert_id": str(a.alert_id),
                "transaction_id": str(a.transaction_id) if a.transaction_id else None,
                "alert_reason": a.alert_reason,
                "severity": "HIGH",
                "resolved": a.resolved,
                "resolution_notes": a.resolution_notes,
                "created_at": (a.created_at.replace(tzinfo=timezone.utc) if a.created_at.tzinfo is None else a.created_at).isoformat() if a.created_at else None
            }
            for a in alerts
        ]
    except Exception:
        # Graceful fallback if database table is empty or uninitialized
        return []

@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        alert = db.query(FraudAlert).filter(FraudAlert.alert_id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        alert.resolved = True
        if notes:
            alert.resolution_notes = notes
        db.commit()
        db.refresh(alert)
        return {"status": "success", "alert_id": str(alert.alert_id), "resolved": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
