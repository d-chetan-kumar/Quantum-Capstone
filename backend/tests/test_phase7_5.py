import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.replay_service import replay_service
from app.scripts.seed_paysim_demo import seed_paysim_demo

client = TestClient(app)

def test_database_health_check():
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_replay_status_endpoint():
    response = client.get("/api/v1/simulator/replay/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_replaying" in data
    assert "processed" in data
    assert "total" in data

def test_replay_start_stop():
    # Test starting replay
    res_start = client.post("/api/v1/simulator/replay/start", json={"speed": 2})
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "started"

    # Test stopping replay
    res_stop = client.post("/api/v1/simulator/replay/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] in ["stopped", "ok"]

def test_seed_paysim_demo_idempotency():
    res = seed_paysim_demo(num_sample=10, random_state=42)
    assert "imported" in res
    assert "skipped" in res
