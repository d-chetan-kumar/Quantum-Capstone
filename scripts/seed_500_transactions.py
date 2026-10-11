import os
import sys
import time
import random
from datetime import datetime, timedelta, timezone

# Ensure backend root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.session import SessionLocal, init_db
from app.models.transaction import Transaction
from app.models.prediction import ModelPrediction
from app.models.alert import FraudAlert
from app.services.ml_service import ml_service
from app.ml.vqc_service import vqc_service
from app.services.risk_engine import risk_engine

def seed_to_target(target_total=525):
    init_db()
    db = SessionLocal()
    
    current_count = db.query(Transaction).count()
    print(f"Current transaction count in database: {current_count}")
    
    needed = max(0, target_total - current_count)
    if needed == 0:
        print(f"Target of {target_total} already satisfied!")
        db.close()
        return current_count
        
    print(f"Generating and evaluating {needed} additional realistic transactions...")
    
    types = ["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"]
    locations = [
        "Mumbai, IN", "Delhi, IN", "Bengaluru, IN", "Hyderabad, IN",
        "Chennai, IN", "Kolkata, IN", "Pune, IN", "Ahmedabad, IN",
        "Singapore, SG", "Dubai, UAE", "London, UK", "New York, US"
    ]
    
    # Establish pool of frequent senders and receivers for account discovery
    senders_safe = [f"C_USER_{i:04d}" for i in range(1, 80)]
    senders_susp = [f"C_FLAG_{i:04d}" for i in range(1, 30)]
    merchants = [f"M_MERCH_{i:04d}" for i in range(1, 60)]
    receivers_ind = [f"C_BENEF_{i:04d}" for i in range(1, 50)]
    
    now = datetime.now(timezone.utc)
    
    added = 0
    safe_cnt = 0
    review_cnt = 0
    alert_cnt = 0
    
    for i in range(needed):
        # 20% suspicious / high-value, 80% regular transactions
        is_suspicious_profile = (random.random() < 0.22)
        
        if is_suspicious_profile:
            tx_type = random.choice(["TRANSFER", "CASH_OUT"])
            amount = round(random.uniform(40000.0, 480000.0), 2)
            sender_id = random.choice(senders_susp)
            receiver_id = random.choice(receivers_ind)
            oldbalanceOrg = amount + round(random.uniform(0.0, 5000.0), 2)
            newbalanceOrig = 0.0
            oldbalanceDest = round(random.uniform(0.0, 10000.0), 2)
            newbalanceDest = oldbalanceDest + amount
        else:
            tx_type = random.choice(["PAYMENT", "CASH_IN", "DEBIT", "PAYMENT"])
            amount = round(random.uniform(25.0, 9500.0), 2)
            sender_id = random.choice(senders_safe)
            receiver_id = random.choice(merchants if tx_type == "PAYMENT" else receivers_ind)
            oldbalanceOrg = amount + round(random.uniform(500.0, 50000.0), 2)
            newbalanceOrig = round(oldbalanceOrg - amount, 2)
            oldbalanceDest = round(random.uniform(100.0, 20000.0), 2)
            newbalanceDest = oldbalanceDest + amount
            
        step = random.randint(1, 200)
        # Distribute timestamps across the last 21 days
        tx_time = now - timedelta(days=random.uniform(0.05, 21.0))
        location = random.choice(locations)
        
        tx = Transaction(
            transaction_type=tx_type,
            amount=amount,
            sender_id=sender_id,
            receiver_id=receiver_id,
            location=location,
            status="processed",
            is_simulated=False,
            timestamp=tx_time,
            created_at=tx_time
        )
        db.add(tx)
        db.flush()
        
        # Build features for real models
        tx_dict = {
            "type": tx_type,
            "amount": amount,
            "step": step,
            "oldbalanceOrg": oldbalanceOrg,
            "newbalanceOrig": newbalanceOrig,
            "oldbalanceDest": oldbalanceDest,
            "newbalanceDest": newbalanceDest
        }
        
        t0 = time.time()
        xgb_res = ml_service.predict(tx_dict)
        p_xgb = float(xgb_res.get("fraud_probability", 0.0))
        
        if vqc_service.is_available():
            vqc_res = vqc_service.predict(tx_dict)
            if isinstance(vqc_res, tuple):
                p_vqc = float(vqc_res[0])
            elif isinstance(vqc_res, dict):
                p_vqc = float(vqc_res.get("quantum_fraud_probability", vqc_res.get("fraud_probability", 0.0)))
            else:
                p_vqc = float(vqc_res)
        else:
            p_vqc = p_xgb
            
        risk_res = risk_engine.compute_risk(p_xgb, p_vqc)
        p_hybrid = float(risk_res.get("hybrid_probability", 0.0))
        risk_level = risk_res.get("risk_level", "SAFE")
        exec_ms = round((time.time() - t0) * 1000, 2)
        
        if risk_level == "SAFE":
            safe_cnt += 1
        elif risk_level == "REVIEW":
            review_cnt += 1
        else:
            alert_cnt += 1
            
        pred = ModelPrediction(
            transaction_id=tx.transaction_id,
            model_name="Hybrid (XGBoost 0.5 + VQC 0.5)",
            model_version="v1.0",
            fraud_probability=p_xgb,
            quantum_probability=p_vqc,
            hybrid_probability=p_hybrid,
            final_risk_score=p_hybrid,
            risk_level=risk_level,
            predicted_class=1 if risk_level == "ALERT" else 0,
            execution_time_ms=exec_ms,
            created_at=tx_time
        )
        db.add(pred)
        
        if risk_level == "ALERT":
            alert = FraudAlert(
                transaction_id=tx.transaction_id,
                alert_reason=f"Hybrid Risk Score {p_hybrid:.4f} exceeded threshold (>=0.70)",
                resolved=(random.random() < 0.25),
                resolution_notes="Flagged by real-time QuantumFraud detection engine." if random.random() < 0.25 else None,
                created_at=tx_time
            )
            db.add(alert)
            
        added += 1
        if added % 100 == 0:
            db.commit()
            print(f"Processed {added}/{needed} transactions (Total so far: {current_count + added})")
            
    db.commit()
    final_total = db.query(Transaction).count()
    alert_total = db.query(FraudAlert).count()
    print(f"\nSeeding complete!")
    print(f"New transactions added: {added}")
    print(f"Final total transactions in database: {final_total}")
    print(f"Total fraud alerts: {alert_total}")
    print(f"Decisions breakdown: SAFE={safe_cnt}, REVIEW={review_cnt}, ALERT={alert_cnt}")
    db.close()
    return final_total

if __name__ == "__main__":
    target = 525
    if len(sys.argv) > 1:
        target = int(sys.argv[1])
    seed_to_target(target)
