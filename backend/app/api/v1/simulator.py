from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.db.session import SessionLocal
from app.services.payment_service import payment_service

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount in INR")
    transaction_type: str = Field(..., description="Type of transaction: CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER")
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None

from app.services.replay_service import replay_service
from app.scripts.seed_paysim_demo import seed_paysim_demo

class ReplayStartRequest(BaseModel):
    speed: int = Field(default=1, ge=1, le=5, description="Replay speed multiplier (1x, 2x, 5x)")

@router.post("/payment")
async def simulate_payment(req: PaymentRequest, db: Session = Depends(get_db)):
    try:
        # Pass optional DB session for persistence if DB is connected
        res = await payment_service.process_payment(
            amount=req.amount,
            transaction_type=req.transaction_type,
            sender_id=req.sender_id,
            receiver_id=req.receiver_id,
            db=db
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment simulation processing error: {str(e)}")

@router.post("/replay/start")
async def start_replay(req: ReplayStartRequest = Body(default=ReplayStartRequest())):
    res = await replay_service.start_replay(speed=req.speed)
    return res

@router.post("/replay/stop")
async def stop_replay():
    res = await replay_service.stop_replay()
    return res

@router.get("/replay/status")
def get_replay_status():
    return replay_service.get_status()

@router.post("/seed")
def seed_demo_data():
    try:
        res = seed_paysim_demo()
        return {"status": "success", "summary": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding error: {str(e)}")
