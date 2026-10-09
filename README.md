# ⚛️ QuantumFraud — Quantum-Assisted Real-Time Payment Fraud Detection

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![Qiskit](https://img.shields.io/badge/Qiskit-1.3.0-6929C4.svg?style=flat&logo=qiskit)](https://qiskit.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0.3-EC4899.svg?style=flat)](https://xgboost.readthedocs.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1.svg?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Python Tests](https://img.shields.io/badge/PyTest-30%20Passed-emerald.svg?style=flat)](./backend/tests)

**QuantumFraud** is an enterprise-grade hybrid quantum-classical payment fraud detection platform. It combines gradient-boosted decision trees (**XGBoost**), a 4-qubit **Variational Quantum Classifier (VQC)** parameterized with `ZZFeatureMap` and `RealAmplitudes`, an optimal 30% / 70% weighted **Hybrid Risk Engine**, and **Automatic Account Discovery & Behavioural Analysis**.

---

## 🌟 Key Features

- **Hybrid Quantum-Classical Risk Engine**: Merges classical gradient boosting (30% weight) with quantum statevector classifier inference (70% weight) for optimal fraud detection recall ($91.0\%$).
- **Variational Quantum Classifier (VQC)**: Built on Qiskit 1.3 with a 4-qubit quantum circuit employing 2-repetition `ZZFeatureMap` data encoding and `RealAmplitudes` ansatz.
- **Automatic Account Discovery**: Automatically tracks sender and receiver account histories, roles (`SENDER`, `RECEIVER`), transaction counts, and baseline metrics without requiring manual registration.
- **Historical Behavioural Risk Analysis**: Computes point-in-time sender amount deviation ratios ($x\times$ historical mean), 24-hour transaction burst rates, and receiver historical fraud alert records with strict data leakage prevention.
- **Real-Time WebSocket Stream**: Streams processed payments and instant `FRAUD_ALERT` events to a live dashboard via WebSockets.
- **Timezone-Aware IST Formatting**: Formats all timestamps in `Asia/Kolkata` (IST, UTC+05:30) with explicit timezone offsets.
- **Durable System of Record**: PostgreSQL 15 primary database with volume persistence and fallback SQLite configuration.

---

## 🏗️ System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │      React + Vite + TypeScript UI       │
                    │ (Dashboard, Live Stream, Investigation) │
                    └────────────────────┬────────────────────┘
                                         │ REST API / WebSocket
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │       FastAPI Backend Gateway           │
                    └────┬──────────────────┬─────────────┬───┘
                         │                  │             │
       ┌─────────────────┴─┐              ┌─┴──────────┐  │
       ▼                   ▼              ▼            ▼  ▼
┌──────────────┐  ┌──────────────────┐ ┌──────────────┐ ┌───────────────────┐
│ XGBoost Model│  │ Quantum VQC (4Q) │ │ Behavioural  │ │ PostgreSQL 15 DB  │
│ Classical ML │  │ Qiskit Simulator │ │ Risk Service │ │ Durable Storage   │
└──────────────┘  └──────────────────┘ └──────────────┘ └───────────────────┘
```

---

## 📊 Benchmark Results & Performance Metrics

Benchmarked across 100 sample payment evaluations (`python scripts/benchmark.py`):

| Component / Pipeline | Avg Latency (ms) | P50 Latency (ms) | P95 Latency (ms) | P99 Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| **Classical XGBoost Model** | **41.94 ms** | 42.38 ms | 47.99 ms | 52.70 ms |
| **Quantum VQC Simulator (4 Qubits)** | **41.71 ms** | 42.59 ms | 48.06 ms | 50.65 ms |
| **Hybrid Risk Combination Engine** | **0.01 ms** | 0.01 ms | 0.01 ms | 0.02 ms |
| **Behavioural Risk & Discovery** | **31.95 ms** | 29.47 ms | 47.29 ms | 67.11 ms |
| **End-to-End Processing Pipeline** | **45.07 ms** | 45.34 ms | 52.20 ms | 58.33 ms |

- **Estimated Throughput**: **22.19 transactions / second** (single CPU core execution).
- **Hybrid Decision Thresholds**:
  - `SAFE`: Score $< 0.30$
  - `REVIEW`: Score $0.30 \le s < 0.70$
  - `ALERT`: Score $\ge 0.70$

---

## 🛠️ Project Structure

```
QUANTUM FRAUD DETECTION/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # REST Endpoints (transactions, models, alerts, accounts, analytics)
│   │   ├── core/               # Configuration settings
│   │   ├── db/                 # Database engine, session, & migrations
│   │   ├── ml/                 # XGBoost & Qiskit VQC service modules
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas with timezone-aware ISO serializers
│   │   └── services/           # Payment service, risk engine, & behavioural risk service
│   ├── tests/                  # PyTest test suite (30 passed tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # UI components & badges
│   │   ├── hooks/              # WebSocket hook
│   │   ├── pages/              # Dashboard, Transactions, Risk Analysis, Simulator, VQCLab
│   │   └── utils/              # IST date formatter (dateUtils.ts)
│   └── package.json
├── docker-compose.yml          # Container orchestration with PostgreSQL volume persistence
├── scripts/
│   └── benchmark.py            # Latency & throughput benchmark script
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Python 3.13 tested)
- **Node.js 18+** & **npm**
- **Docker & Docker Compose** (Optional, for PostgreSQL database)

### Option 1: Local Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/quantum-fraud.git
   cd quantum-fraud
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

### Option 2: Docker Compose Deployment

```bash
docker-compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: Port `5432` with `postgres_data` persistent volume.

---

## 🧪 Testing & Benchmarking

### Run Backend Unit & Integration Tests
```bash
cd backend
python -m pytest
```
*Output: 30 passed in ~28s.*

### Run System Benchmark
```bash
python scripts/benchmark.py
```
*Exports detailed JSON latency breakdown to `artifacts/benchmark_results.json`.*

### Verify Frontend TypeScript Build
```bash
cd frontend
npm run build
```
*Output: 0 TypeScript errors.*

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health & active database backend type |
| `GET` | `/api/v1/transactions/` | Paginated transaction explorer list |
| `GET` | `/api/v1/transactions/{id}` | Single transaction details |
| `GET` | `/api/v1/transactions/{id}/risk` | Combined hybrid risk evaluation |
| `GET` | `/api/v1/transactions/{id}/behaviour` | Automatic account discovery & behavioural risk analysis |
| `POST` | `/api/v1/simulator/payment` | Submit & process simulated payment |
| `GET` | `/api/v1/accounts/{id}/profile` | Account discovery profile & historical metrics |
| `GET` | `/api/v1/alerts` | Fraud risk alerts list |
| `WS` | `/ws/v1/stream` | Real-time WebSocket event stream |

---

## 📜 License

Distributed under the **MIT License**.
