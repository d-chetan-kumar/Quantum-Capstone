# System Architecture

## Overview
The Quantum-Assisted Real-Time Payment Fraud Detection & Authentication Platform is a hybrid system combining classical machine learning and quantum computing (VQC) to analyze payment transactions in real-time.

## High-Level Flow
1. **User / Payment Simulator:** Initiates a payment request.
2. **Transaction Validation:** Backend validates the payload.
3. **Feature Engineering:** Raw data is processed into features.
4. **Classical AI & Quantum AI Inference:** Parallel execution of classical (e.g., XGBoost) and quantum (e.g., VQC via Qiskit) models.
5. **Hybrid Risk Engine:** Combines classical and quantum probabilities.
6. **Risk Classification:** Final fraud risk score is calculated (SAFE / REVIEW / ALERT).
7. **PostgreSQL:** Transaction and prediction details are persisted.
8. **WebSocket:** Real-time event is emitted to connected clients.
9. **React Frontend:** Updates the UI immediately.

## Tech Stack
- **Frontend:** React, Vite, TypeScript, Tailwind CSS, Framer Motion, Lucide React, Recharts.
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy.
- **Database:** PostgreSQL.
- **Machine Learning:** scikit-learn, XGBoost.
- **Quantum:** Qiskit.
- **Real-time:** FastAPI WebSockets.
- **Infrastructure:** Docker Compose.

## Project Structure
```text
frontend/     # React frontend application
backend/      # FastAPI backend application
ml/           # Classical machine learning pipeline and models
quantum/      # Quantum algorithms and VQC implementation
models/       # Saved model artifacts
data/         # Datasets and preprocessing scripts
scripts/      # Utility scripts for training and simulation
tests/        # Unit and integration tests
docs/         # Project documentation and methodology
```
