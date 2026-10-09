# Database Design (PostgreSQL)

## Tables Overview

### 1. `transactions`
- `transaction_id` (UUID, Primary Key)
- `timestamp` (DateTime)
- `amount` (Decimal)
- `transaction_type` (String)
- `sender_id` (String)
- `receiver_id` (String)
- `location` (String)
- `status` (String)
- `created_at` (DateTime)

### 2. `model_predictions`
- `prediction_id` (UUID, Primary Key)
- `transaction_id` (UUID, Foreign Key)
- `classical_probability` (Float)
- `quantum_probability` (Float)
- `hybrid_probability` (Float)
- `final_risk_score` (Float)
- `risk_level` (String: SAFE, REVIEW, ALERT)
- `execution_time_ms` (Float)
- `created_at` (DateTime)

### 3. `fraud_alerts`
- `alert_id` (UUID, Primary Key)
- `transaction_id` (UUID, Foreign Key)
- `alert_reason` (String)
- `resolved` (Boolean)
- `resolution_notes` (Text)
- `created_at` (DateTime)

### 4. `simulation_runs`
- `simulation_id` (UUID, Primary Key)
- `start_time` (DateTime)
- `end_time` (DateTime)
- `transactions_generated` (Integer)
- `configuration` (JSON)

### 5. `model_evaluations`
- `evaluation_id` (UUID, Primary Key)
- `model_type` (String: classical, quantum, hybrid)
- `accuracy` (Float)
- `precision` (Float)
- `recall` (Float)
- `f1_score` (Float)
- `confusion_matrix` (JSON)
- `evaluated_at` (DateTime)

### 6. `system_events`
- `event_id` (UUID, Primary Key)
- `event_type` (String)
- `details` (JSON)
- `timestamp` (DateTime)
