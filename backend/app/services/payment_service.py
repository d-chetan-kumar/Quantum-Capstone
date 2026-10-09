import time
import uuid
import asyncio
import random
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.risk_engine import risk_engine
from app.services.realtime_service import realtime_manager

VALID_TYPES = {"CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"}

class PaymentService:
    async def process_payment(
        self,
        amount: float,
        transaction_type: str,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        # 1. Input Validation
        if amount <= 0:
            raise ValueError("Payment amount must be greater than 0")

        tx_type_upper = transaction_type.upper()
        if tx_type_upper not in VALID_TYPES:
            raise ValueError(f"Invalid transaction type '{transaction_type}'. Must be one of {sorted(list(VALID_TYPES))}")

        sender = (sender_id.strip() if sender_id and sender_id.strip() else f"C{random.randint(10000000, 99999999)}")
        receiver = (receiver_id.strip() if receiver_id and receiver_id.strip() else f"C{random.randint(10000000, 99999999)}")

        if sender == receiver:
            raise ValueError("Sender ID and Receiver ID cannot be identical.")

        tx_id = str(uuid.uuid4())
        t0 = time.time()

        tx_dict = {
            "amount": amount,
            "type": tx_type_upper,
            "transaction_type": tx_type_upper,
            "sender_id": sender,
            "receiver_id": receiver,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 2. Model Inference & Hybrid Risk Engine Evaluation
        risk_res = risk_engine.evaluate_transaction(tx_dict, tx_id, db=db)
        proc_time_ms = round((time.time() - t0) * 1000, 2)

        # 3. Database Persistence (Transaction, ModelPrediction, FraudAlert)
        persisted = False
        own_session = False
        if db is None:
            from app.db.session import SessionLocal
            db = SessionLocal()
            own_session = True

        try:
            from app.models.transaction import Transaction
            from app.models.prediction import ModelPrediction
            from app.models.alert import FraudAlert

            now_utc = datetime.now(timezone.utc)

            # Check if transaction already created
            tx_obj = db.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
            if not tx_obj:
                tx_obj = Transaction(
                    transaction_id=tx_id,
                    sender_id=sender,
                    receiver_id=receiver,
                    amount=amount,
                    transaction_type=tx_type_upper,
                    status="processed",
                    is_simulated=True,
                    timestamp=now_utc,
                    created_at=now_utc,
                    updated_at=now_utc
                )
                db.add(tx_obj)

            # Persist ModelPrediction record
            pred_obj = ModelPrediction(
                transaction_id=tx_id,
                model_name="Hybrid (XGBoost 0.3 + VQC 0.7)",
                model_version="v1.0",
                fraud_probability=risk_res["classical_probability"],
                quantum_probability=risk_res["quantum_probability"],
                hybrid_probability=risk_res["hybrid_probability"],
                final_risk_score=risk_res["hybrid_probability"],
                risk_level=risk_res["risk_level"],
                predicted_class=1 if risk_res["risk_level"] == "ALERT" else 0,
                execution_time_ms=proc_time_ms,
                created_at=now_utc
            )
            db.add(pred_obj)

            # Persist FraudAlert record if risk_level == "ALERT"
            if risk_res["risk_level"] == "ALERT":
                existing_alert = db.query(FraudAlert).filter(FraudAlert.transaction_id == tx_id).first()
                if not existing_alert:
                    alert_obj = FraudAlert(
                        transaction_id=tx_id,
                        alert_reason=f"High hybrid fraud risk score ({risk_res['hybrid_probability']:.4f})",
                        resolved=False,
                        created_at=now_utc
                    )
                    db.add(alert_obj)

            db.commit()
            persisted = True
        except Exception as e:
            if db: db.rollback()
            print(f"Database transaction persistence error: {e}")
        finally:
            if own_session and db:
                db.close()

        # 4. Construct Real-Time Event Schema
        event_payload = {
            "event": "payment.processed",
            "transaction_id": tx_id,
            "amount": float(amount),
            "transaction_type": tx_type_upper,
            "sender_id": sender,
            "receiver_id": receiver,
            "classical_probability": risk_res["classical_probability"],
            "quantum_probability": risk_res["quantum_probability"],
            "hybrid_probability": risk_res["hybrid_probability"],
            "risk_level": risk_res["risk_level"],
            "status": "processed",
            "timestamp": risk_res["created_at"],
            "processing_time_ms": proc_time_ms,
            "persisted": persisted
        }

        # 5. Broadcast Event over WebSocket
        try:
            await realtime_manager.broadcast(event_payload)
            if risk_res["risk_level"] == "ALERT":
                alert_event = {
                    "event": "fraud.alert",
                    "transaction_id": tx_id,
                    "amount": float(amount),
                    "risk_level": "ALERT",
                    "hybrid_probability": risk_res["hybrid_probability"],
                    "alert_reason": f"High hybrid fraud risk score ({risk_res['hybrid_probability']:.4f})",
                    "timestamp": risk_res["created_at"]
                }
                await realtime_manager.broadcast(alert_event)
        except Exception as e:
            print(f"WebSocket broadcast error: {e}")

        return {
            "transaction_id": tx_id,
            "status": "processed",
            "amount": float(amount),
            "transaction_type": tx_type_upper,
            "sender_id": sender,
            "receiver_id": receiver,
            "classical_probability": risk_res["classical_probability"],
            "quantum_probability": risk_res["quantum_probability"],
            "hybrid_probability": risk_res["hybrid_probability"],
            "risk_level": risk_res["risk_level"],
            "processing_time_ms": proc_time_ms,
            "created_at": risk_res["created_at"],
            "persisted": persisted
        }

payment_service = PaymentService()

