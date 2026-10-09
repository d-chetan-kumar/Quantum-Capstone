import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, init_db
from app.models.transaction import Transaction
from app.models.alert import FraudAlert
from app.services.behavioural_risk_service import behavioural_risk_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield

def test_newly_observed_accounts():
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sender_id = f"C_NEW_{uid}"
        receiver_id = f"M_NEW_{uid}"

        profile = behavioural_risk_service.get_account_profile(sender_id, db=db)
        assert profile["is_known"] is False
        assert profile["history_status"] == "NEWLY_OBSERVED"
        assert profile["total_transactions_count"] == 0

        sender_b = behavioural_risk_service.compute_sender_behaviour(sender_id, current_amount=1000.0, db=db)
        assert sender_b["history_status"] == "NEWLY_OBSERVED"
        assert sender_b["previous_tx_count"] == 0
        assert sender_b["amount_deviation_ratio"] == 1.0
    finally:
        db.close()

def test_data_leakage_prevention_and_repeated_transactions():
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sender_id = f"C_LEAK_{uid}"
        receiver_id = f"M_LEAK_{uid}"

        t1 = Transaction(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=10000.0,
            transaction_type="TRANSFER",
            status="processed",
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        t2 = Transaction(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=20000.0,
            transaction_type="TRANSFER",
            status="processed",
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        t3_current = Transaction(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=50000.0,
            transaction_type="TRANSFER",
            status="processed",
            created_at=datetime.now(timezone.utc)
        )
        db.add_all([t1, t2, t3_current])
        db.commit()

        # Calculate metrics for t3_current (excluding t3_current itself)
        sender_b = behavioural_risk_service.compute_sender_behaviour(
            sender_id=sender_id,
            current_amount=50000.0,
            current_tx_id=t3_current.transaction_id,
            as_of_time=t3_current.created_at,
            db=db
        )

        # Must exclude t3_current: previous count should be 2, avg should be 15000 (sum 30000 / 2)
        assert sender_b["previous_tx_count"] == 2
        assert sender_b["total_sent_amount"] == 30000.0
        assert sender_b["avg_sent_amount"] == 15000.0
        # Amount deviation ratio: 50000 / 15000 = 3.33x
        assert sender_b["amount_deviation_ratio"] == 3.33
        # Baseline threshold is 3, so 2 transactions = INSUFFICIENT_HISTORY
        assert sender_b["history_status"] == "INSUFFICIENT_HISTORY"
    finally:
        db.close()

def test_amount_deviation_and_sufficient_history():
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sender_id = f"C_SUFF_{uid}"
        receiver_id = f"M_SUFF_{uid}"

        base_time = datetime.now(timezone.utc) - timedelta(days=10)
        # Create 3 historical transactions to satisfy threshold >= 3
        txs = [
            Transaction(sender_id=sender_id, receiver_id=receiver_id, amount=10000.0, transaction_type="PAYMENT", status="processed", created_at=base_time + timedelta(days=i))
            for i in range(3)
        ]
        db.add_all(txs)
        db.commit()

        curr_tx = Transaction(sender_id=sender_id, receiver_id=receiver_id, amount=60000.0, transaction_type="PAYMENT", status="processed", created_at=datetime.now(timezone.utc))
        db.add(curr_tx)
        db.commit()

        eval_res = behavioural_risk_service.evaluate_transaction_behaviour(curr_tx.transaction_id, db=db)
        
        assert eval_res["sender"]["history_status"] == "SUFFICIENT_HISTORY"
        assert eval_res["sender"]["previous_tx_count"] == 3
        assert eval_res["sender"]["avg_sent_amount"] == 10000.0
        assert eval_res["sender"]["amount_deviation_ratio"] == 6.0
        assert eval_res["behavioural_risk_signal"] in ["SUSPICIOUS", "ELEVATED"]

        # Verify indicator details
        codes = [ind["code"] for ind in eval_res["indicators"]]
        assert "HIGH_AMOUNT_DEVIATION" in codes
    finally:
        db.close()

def test_receiver_historical_fraud_evidence():
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sender_id = f"C_NORM_{uid}"
        receiver_id = f"M_BAD_{uid}"

        # Prior transaction to bad receiver that triggered a fraud alert
        prior_tx = Transaction(sender_id=f"C_VIC_{uid}", receiver_id=receiver_id, amount=100000.0, transaction_type="TRANSFER", status="processed", created_at=datetime.now(timezone.utc) - timedelta(days=5))
        db.add(prior_tx)
        db.flush()

        alert = FraudAlert(transaction_id=prior_tx.transaction_id, alert_reason="High risk alert", resolved=False, created_at=datetime.now(timezone.utc) - timedelta(days=5))
        db.add(alert)
        db.commit()

        # Current transaction to the same bad receiver
        curr_tx = Transaction(sender_id=sender_id, receiver_id=receiver_id, amount=5000.0, transaction_type="TRANSFER", status="processed", created_at=datetime.now(timezone.utc))
        db.add(curr_tx)
        db.commit()

        eval_res = behavioural_risk_service.evaluate_transaction_behaviour(curr_tx.transaction_id, db=db)
        
        assert eval_res["receiver"]["unresolved_alerts_count"] == 1
        codes = [ind["code"] for ind in eval_res["indicators"]]
        assert "RECEIVER_WITH_ACTIVE_ALERTS" in codes
    finally:
        db.close()

def test_behavioural_endpoint():
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        tx = Transaction(sender_id=f"C_EP_{uid}", receiver_id=f"M_EP_{uid}", amount=2500.0, transaction_type="PAYMENT", status="processed", created_at=datetime.now(timezone.utc))
        db.add(tx)
        db.commit()
        tx_id = tx.transaction_id
    finally:
        db.close()

    res = client.get(f"/api/v1/transactions/{tx_id}/behaviour")
    assert res.status_code == 200
    data = res.json()
    assert "sender" in data
    assert "receiver" in data
    assert "behavioural_risk_signal" in data
    assert "indicators" in data

def test_account_profile_endpoint():
    uid = uuid.uuid4().hex[:8]
    acc_id = f"C_EP_{uid}"
    res = client.get(f"/api/v1/accounts/{acc_id}/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["account_id"] == acc_id
    assert "history_status" in data
    assert "sender_metrics" in data

