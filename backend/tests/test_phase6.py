import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.services.payment_service import payment_service
from app.services.realtime_service import realtime_manager

client = TestClient(app)

def test_payment_simulator_endpoint():
    payload = {
        "amount": 15000.0,
        "transaction_type": "TRANSFER",
        "sender_id": "C99988877",
        "receiver_id": "C11122233"
    }
    response = client.post("/api/v1/simulator/payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "transaction_id" in data
    assert data["status"] == "processed"
    assert data["amount"] == 15000.0
    assert data["transaction_type"] == "TRANSFER"
    assert 0.0 <= data["classical_probability"] <= 1.0
    assert 0.0 <= data["quantum_probability"] <= 1.0
    assert 0.0 <= data["hybrid_probability"] <= 1.0
    assert data["risk_level"] in ("SAFE", "REVIEW", "ALERT")
    assert "processing_time_ms" in data

def test_invalid_payment_simulator_inputs():
    # Negative amount
    res1 = client.post("/api/v1/simulator/payment", json={"amount": -500.0, "transaction_type": "TRANSFER"})
    assert res1.status_code == 422 # Pydantic validation error gt=0

    # Invalid transaction type
    res2 = client.post("/api/v1/simulator/payment", json={"amount": 100.0, "transaction_type": "INVALID_TYPE"})
    assert res2.status_code == 400

@pytest.mark.anyio
async def test_payment_service_async_processing():
    res = await payment_service.process_payment(
        amount=50000.0,
        transaction_type="CASH_OUT",
        sender_id="C55554444",
        receiver_id="C66667777"
    )
    assert res["status"] == "processed"
    assert res["amount"] == 50000.0
    assert res["risk_level"] in ("SAFE", "REVIEW", "ALERT")
    assert "processing_time_ms" in res

def test_websocket_stream_endpoint():
    with client.websocket_connect("/ws/v1/payments") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "connection.established"
        
        # Test ping-pong keep-alive
        websocket.send_text("ping")
        message = websocket.receive_text()
        assert message == "pong"
