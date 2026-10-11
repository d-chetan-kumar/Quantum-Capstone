import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.models.prediction import ModelPrediction
from app.models.alert import FraudAlert
from app.services.risk_engine import risk_engine
from app.services.payment_service import payment_service
from app.services.behavioural_risk_service import behavioural_risk_service

client = TestClient(app)

def test_boundary_condition_safe():
    # Exactly below 0.30 -> SAFE
    res = risk_engine.compute_risk(0.20, 0.20)
    assert res["hybrid_probability"] < 0.30
    assert res["risk_level"] == "SAFE"
    
    # Boundary just below 0.30
    # 0.3 * 0.299 + 0.7 * 0.299 = 0.299
    res_edge = risk_engine.compute_risk(0.299, 0.299)
    assert res_edge["risk_level"] == "SAFE"

def test_boundary_condition_review_threshold():
    # Exactly at 0.30 -> REVIEW
    res_at_30 = risk_engine.compute_risk(0.30, 0.30)
    assert abs(res_at_30["hybrid_probability"] - 0.30) < 1e-5
    assert res_at_30["risk_level"] == "REVIEW"

    # Middle of review
    res_mid = risk_engine.compute_risk(0.50, 0.50)
    assert res_mid["risk_level"] == "REVIEW"

    # Just below 0.70
    res_below_70 = risk_engine.compute_risk(0.699, 0.699)
    assert res_below_70["risk_level"] == "REVIEW"

def test_boundary_condition_alert_threshold():
    # Exactly at 0.70 -> ALERT
    res_at_70 = risk_engine.compute_risk(0.70, 0.70)
    assert abs(res_at_70["hybrid_probability"] - 0.70) < 1e-5
    assert res_at_70["risk_level"] == "ALERT"

    # High risk
    res_high = risk_engine.compute_risk(0.95, 0.90)
    assert res_high["risk_level"] == "ALERT"

def test_hybrid_clamping():
    # Negative inputs clamped to 0.0
    res_neg = risk_engine.compute_risk(-0.5, 0.0)
    assert res_neg["hybrid_probability"] >= 0.0

    # >1 inputs clamped to 1.0
    res_over = risk_engine.compute_risk(1.5, 1.2)
    assert res_over["hybrid_probability"] <= 1.0

def test_three_decision_categories_on_real_models():
    # 1. Test case yielding SAFE (Low amount DEBIT)
    tx_safe = {'amount': 200.0, 'transaction_type': 'DEBIT', 'timestamp': '2026-10-11T12:00:00Z'}
    eval_safe = risk_engine.evaluate_transaction(tx_safe, 'tx-safe')
    assert eval_safe["risk_level"] == "SAFE"

    # 2. Test case yielding REVIEW (Daytime PAYMENT or CASH_OUT)
    tx_review = {'amount': 5000.0, 'transaction_type': 'CASH_OUT', 'timestamp': '2026-10-11T12:00:00Z'}
    eval_review = risk_engine.evaluate_transaction(tx_review, 'tx-review')
    assert eval_review["risk_level"] == "REVIEW"

    # 3. Test case yielding ALERT (High value TRANSFER)
    tx_alert = {'amount': 50000.0, 'transaction_type': 'TRANSFER', 'timestamp': '2026-10-11T12:00:00Z'}
    eval_alert = risk_engine.evaluate_transaction(tx_alert, 'tx-alert')
    assert eval_alert["risk_level"] == "ALERT"

def test_invalid_input_validation():
    # Negative amount
    resp = client.post("/api/v1/simulator/payment", json={"amount": -100, "transaction_type": "TRANSFER"})
    assert resp.status_code == 422 or resp.status_code == 400

    # Zero amount
    resp = client.post("/api/v1/simulator/payment", json={"amount": 0, "transaction_type": "TRANSFER"})
    assert resp.status_code == 422 or resp.status_code == 400

    # Invalid transaction type
    resp = client.post("/api/v1/simulator/payment", json={"amount": 100, "transaction_type": "INVALID_TYPE"})
    assert resp.status_code == 400

    # Identical sender and receiver
    resp = client.post("/api/v1/simulator/payment", json={
        "amount": 100,
        "transaction_type": "TRANSFER",
        "sender_id": "SAME_ACCT",
        "receiver_id": "SAME_ACCT"
    })
    assert resp.status_code == 400

def test_persistence_and_investigation_consistency():
    db = SessionLocal()
    sender_id = f"C_REG_{uuid.uuid4().hex[:6]}"
    receiver_id = f"M_REG_{uuid.uuid4().hex[:6]}"

    # Submit simulation payment
    payload = {
        "amount": 75000.0,
        "transaction_type": "TRANSFER",
        "sender_id": sender_id,
        "receiver_id": receiver_id
    }
    resp = client.post("/api/v1/simulator/payment", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    tx_id = data["transaction_id"]
    assert data["persisted"] is True
    assert data["processing_time_ms"] > 0

    # 1. Verify Transaction in DB
    db_tx = db.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
    assert db_tx is not None
    assert db_tx.amount == 75000.0
    assert db_tx.transaction_type == "TRANSFER"

    # 2. Verify ModelPrediction in DB
    db_pred = db.query(ModelPrediction).filter(ModelPrediction.transaction_id == tx_id).first()
    assert db_pred is not None
    assert abs(db_pred.hybrid_probability - data["hybrid_probability"]) < 1e-4

    # 3. Verify FraudAlert in DB if ALERT
    if data["risk_level"] == "ALERT":
        db_alert = db.query(FraudAlert).filter(FraudAlert.transaction_id == tx_id).first()
        assert db_alert is not None

    # 4. Verify Investigation /risk endpoint returns exact same numbers
    risk_resp = client.get(f"/api/v1/transactions/{tx_id}/risk")
    assert risk_resp.status_code == 200
    risk_data = risk_resp.json()
    assert abs(risk_data["hybrid_probability"] - data["hybrid_probability"]) < 1e-4
    assert risk_data["risk_level"] == data["risk_level"]
    assert abs(risk_data["classical_probability"] - data["classical_probability"]) < 1e-4
    assert abs(risk_data["quantum_probability"] - data["quantum_probability"]) < 1e-4

    # 5. Verify Behavioural Risk Endpoint
    beh_resp = client.get(f"/api/v1/transactions/{tx_id}/behaviour")
    assert beh_resp.status_code == 200
    beh_data = beh_resp.json()
    assert beh_data["transaction_id"] == tx_id
    assert "sender" in beh_data
    assert "receiver" in beh_data
    assert "indicators" in beh_data

    db.close()
