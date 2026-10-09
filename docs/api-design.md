# API Design (REST)

## Base URL: `/api/v1`

### Health Check
- `GET /health`
  - Returns backend and database connection status.

### Simulator Controls
- `POST /simulator/start`
  - Starts the generation of synthetic payment transactions.
- `POST /simulator/stop`
  - Stops the simulation.
- `GET /simulator/status`
  - Returns current simulation state and configuration.

### Transactions
- `GET /transactions`
  - Retrieves paginated historical transactions.
- `GET /transactions/{transaction_id}`
  - Retrieves full details for a specific transaction.
- `POST /transactions`
  - Manual endpoint for payment initiation (used by the simulator or manual entry).

### Transaction Analysis
- `GET /analysis/{transaction_id}`
  - Retrieves the extracted features, classical/quantum probabilities, and hybrid risk engine results.

### Alerts
- `GET /alerts`
  - Retrieves list of recent fraud alerts (filtered by status).
- `PATCH /alerts/{alert_id}`
  - Update alert resolution status.

### Analytics
- `GET /analytics/dashboard`
  - Aggregated metrics (total volume, fraud rate, system latency) for the UI.

### Models
- `GET /models/metrics`
  - Retrieve evaluation metrics for the classical, quantum, and hybrid models.
