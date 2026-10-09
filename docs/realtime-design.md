# Real-Time WebSocket Design

## Endpoint: `/ws/v1/stream`

## Event Types (Server to Client)

### `transaction_processed`
Emitted immediately after a transaction is fully analyzed and persisted.
```json
{
  "event": "transaction_processed",
  "data": {
    "transaction_id": "uuid",
    "amount": 84532.50,
    "timestamp": "2023-10-25T14:30:00Z",
    "classical_probability": 0.12,
    "quantum_probability": 0.15,
    "hybrid_probability": 0.13,
    "risk_level": "SAFE"
  }
}
```

### `fraud_alert`
Emitted when a transaction is flagged as REVIEW or ALERT.
```json
{
  "event": "fraud_alert",
  "data": {
    "alert_id": "uuid",
    "transaction_id": "uuid",
    "risk_level": "ALERT",
    "reason": "Unusual location and high amount"
  }
}
```

### `simulation_status`
Emitted when simulation starts, stops, or changes rate.
```json
{
  "event": "simulation_status",
  "data": {
    "active": true,
    "rate_per_second": 5,
    "transactions_generated": 1050
  }
}
```

### `system_status`
Emitted periodically or on state change (e.g., model loaded, DB connection issue).
```json
{
  "event": "system_status",
  "data": {
    "status": "healthy",
    "latency_ms": 42
  }
}
```
