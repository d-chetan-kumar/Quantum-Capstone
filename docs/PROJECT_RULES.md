# Project Rules

## Absolute Development Principle: Build the Real Functional System First

1. **NO FAKE DATA:** The frontend must never be built as a collection of mock screens. Every important UI element must have a real backend source.
2. **NO FAKE METRICS:** Do not display fake transaction counts, fraud probabilities, alerts, model metrics, quantum results, or charts.
3. **NO FAKE PREDICTIONS:** All predictions must come from actual model inference.
4. **NO FRONTEND-ONLY SIMULATION:** The real-time simulator must use actual inference through the backend.
5. **PERSISTENCE:** PostgreSQL is the persistent data layer. No in-memory databases for production features.
6. **LIVE EVENTS:** WebSocket is used for live events and real-time updates. The frontend should not repeatedly poll the database.
7. **BACKEND LOGIC:** The backend owns all business logic, model logic, and threshold logic. The frontend must not contain model logic.
8. **DATA INTEGRITY:** Test data cannot influence model training or model selection.
9. **QUANTUM CLAIMS:** All quantum claims must be supported by actual experiments and code using Qiskit.
10. **REPRODUCIBILITY:** Deployment must remain reproducible (e.g., using Docker Compose and environment variables).
11. **HONEST STATES:** If real data does not yet exist, display an honest empty/loading state.
