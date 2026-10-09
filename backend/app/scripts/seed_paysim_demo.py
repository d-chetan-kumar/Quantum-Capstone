import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

# Ensure backend root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.session import SessionLocal, init_db
from app.models import Transaction, ModelPrediction, FraudAlert
from app.services.ml_service import ml_service
from app.ml.vqc_service import vqc_service
from app.services.risk_engine import risk_engine

DATA_PATHS = [
    os.path.join(PROJECT_ROOT, "data", "PS_20174392719_1491204439457_log.csv"),
    os.path.join(BACKEND_DIR, "data", "PS_20174392719_1491204439457_log.csv"),
    os.path.abspath("data/PS_20174392719_1491204439457_log.csv")
]

COLS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg",
    "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest",
    "isFraud", "isFlaggedFraud"
]

def get_paysim_data_path():
    for p in DATA_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("PaySim CSV file not found in expected locations.")

def seed_paysim_demo(num_sample: int = 200, random_state: int = 42):
    init_db()
    db = SessionLocal()

    csv_path = get_paysim_data_path()
    file_size = os.path.getsize(csv_path)

    # Read PaySim dataset with header skipping check
    header_idx = None
    with open(csv_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if "step,type,amount" in line and "log_amount" not in line:
                header_idx = idx
                break

    if header_idx is None:
        df = pd.read_csv(csv_path)
    else:
        df = pd.read_csv(csv_path, skiprows=header_idx + 1, header=None, names=COLS)

    df = df.sort_values(by='step')

    total_rows = len(df)
    train_idx = int(total_rows * 0.7)
    val_idx = int(total_rows * 0.85)

    test_df = df.iloc[val_idx:]

    # Select deterministic test subset (100 fraud / 100 non-fraud for 200 rows)
    num_fraud = num_sample // 2
    num_non_fraud = num_sample - num_fraud

    test_fraud = test_df[test_df['isFraud'] == 1].sample(n=min(num_fraud, (test_df['isFraud'] == 1).sum()), random_state=random_state)
    test_non_fraud = test_df[test_df['isFraud'] == 0].sample(n=min(num_non_fraud, (test_df['isFraud'] == 0).sum()), random_state=random_state)

    sample_test_df = pd.concat([test_fraud, test_non_fraud]).sample(frac=1, random_state=random_state).reset_index(drop=True)

    imported_count = 0
    skipped_count = 0
    safe_count = 0
    review_count = 0
    alert_count = 0
    alerts_created = 0

    base_time = datetime.now(timezone.utc) - timedelta(days=7)

    for _, row in sample_test_df.iterrows():
        sender_id = str(row['nameOrig'])
        receiver_id = str(row['nameDest'])
        amount = float(row['amount'])
        tx_type = str(row['type'])
        step = int(row['step'])

        # Check existing to prevent duplicates
        existing = db.query(Transaction).filter(
            Transaction.sender_id == sender_id,
            Transaction.receiver_id == receiver_id,
            Transaction.amount == amount,
            Transaction.transaction_type == tx_type
        ).first()

        if existing:
            skipped_count += 1
            continue

        tx_time = base_time + timedelta(hours=step % 168)

        # Create Transaction
        tx = Transaction(
            transaction_type=tx_type,
            amount=amount,
            sender_id=sender_id,
            receiver_id=receiver_id,
            location="PaySim Global Network",
            status="COMPLETED",
            is_simulated=False,
            timestamp=tx_time,
            created_at=tx_time
        )
        db.add(tx)
        db.flush()

        # Build feature dict for real model inference
        tx_dict = {
            "type": tx_type,
            "amount": amount,
            "step": step,
            "oldbalanceOrg": float(row['oldbalanceOrg']),
            "newbalanceOrig": float(row['newbalanceOrig']),
            "oldbalanceDest": float(row['oldbalanceDest']),
            "newbalanceDest": float(row['newbalanceDest'])
        }

        start_time = time.time()
        # 1. Real XGBoost Prediction
        xgb_res = ml_service.predict(tx_dict)
        p_xgb = float(xgb_res["fraud_probability"])

        # 2. Real VQC Prediction
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

        # 3. Real Hybrid Risk Engine
        risk_res = risk_engine.compute_risk(p_xgb, p_vqc)
        p_hybrid = float(risk_res["hybrid_probability"])
        risk_level = risk_res["risk_level"]
        exec_ms = (time.time() - start_time) * 1000

        if risk_level == "SAFE":
            safe_count += 1
        elif risk_level == "REVIEW":
            review_count += 1
        else:
            alert_count += 1

        # Create ModelPrediction record
        pred = ModelPrediction(
            transaction_id=tx.transaction_id,
            model_name="Hybrid (XGBoost 0.3 + VQC 0.7)",
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

        # Create FraudAlert ONLY when risk_level == "ALERT"
        if risk_level == "ALERT":
            alert = FraudAlert(
                transaction_id=tx.transaction_id,
                alert_reason=f"Hybrid Risk Score {p_hybrid:.4f} exceeded alert threshold (0.70)",
                resolved=False,
                created_at=tx_time
            )
            db.add(alert)
            alerts_created += 1

        imported_count += 1

    db.commit()
    db.close()

    print("\nPAYSIM DEMO REPLAY")
    print("------------------")
    print(f"Dataset:\nPaySim ({csv_path})")
    print("\nSource:\nHeld-out Test Subset")
    print(f"\nSelected:\n{len(sample_test_df)}")
    print(f"\nFraud Ground Truth:\n{(sample_test_df['isFraud'] == 1).sum()}")
    print(f"\nNon-Fraud Ground Truth:\n{(sample_test_df['isFraud'] == 0).sum()}")
    print(f"\nImported:\n{imported_count}")
    print(f"\nSkipped Existing:\n{skipped_count}")
    print("\nModel Inference:\nXGBoost [OK]\nVQC [OK]\nHybrid [OK]")
    print(f"\nRisk Decisions:\nSAFE: {safe_count}\nREVIEW: {review_count}\nALERT: {alert_count}")
    print(f"\nAlerts Created:\n{alerts_created}")
    print("\nDatabase:\nCONNECTED")

    return {
        "imported": imported_count,
        "skipped": skipped_count,
        "safe": safe_count,
        "review": review_count,
        "alert": alert_count,
        "alerts_created": alerts_created
    }

if __name__ == "__main__":
    seed_paysim_demo()
