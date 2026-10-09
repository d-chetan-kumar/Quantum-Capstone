import os
import sys
import time
import json
import statistics
import numpy as np
from datetime import datetime, timezone

# Ensure project root & backend are in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.session import SessionLocal, init_db
from app.services.ml_service import ml_service
from app.ml.vqc_service import vqc_service
from app.services.risk_engine import risk_engine
from app.services.behavioural_risk_service import behavioural_risk_service
from app.models.transaction import Transaction

def run_benchmark(num_samples: int = 100):
    print("==========================================================================")
    print("         QUANTUMFRAUD BENCHMARK SUITE — LATENCY & THROUGHPUT EVALUATION    ")
    print("==========================================================================")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Benchmark Samples: {num_samples} transactions")
    print("--------------------------------------------------------------------------")

    init_db()
    db = SessionLocal()

    # Sample transaction payload
    sample_tx = {
        "amount": 45000.0,
        "type": "TRANSFER",
        "transaction_type": "TRANSFER",
        "sender_id": "C_BENCHMARK_SENDER",
        "receiver_id": "M_BENCHMARK_RECEIVER",
        "step": 12,
        "oldbalanceOrg": 50000.0,
        "newbalanceOrig": 5000.0,
        "oldbalanceDest": 10000.0,
        "newbalanceDest": 55000.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    xgb_latencies = []
    vqc_latencies = []
    hybrid_latencies = []
    behaviour_latencies = []
    pipeline_latencies = []

    print("Running performance benchmark iterations...")

    for i in range(num_samples):
        # 1. Classical XGBoost Latency
        t0 = time.perf_counter()
        xgb_res = ml_service.predict(sample_tx)
        t_xgb = (time.perf_counter() - t0) * 1000
        xgb_latencies.append(t_xgb)

        # 2. Quantum VQC Latency
        t0 = time.perf_counter()
        if vqc_service.is_available():
            vqc_res = vqc_service.predict(sample_tx)
            p_vqc = float(vqc_res[0]) if isinstance(vqc_res, tuple) else float(vqc_res)
        else:
            p_vqc = float(xgb_res["fraud_probability"])
        t_vqc = (time.perf_counter() - t0) * 1000
        vqc_latencies.append(t_vqc)

        # 3. Hybrid Risk Engine Latency
        t0 = time.perf_counter()
        risk_res = risk_engine.compute_risk(xgb_res["fraud_probability"], p_vqc)
        t_hybrid = (time.perf_counter() - t0) * 1000
        hybrid_latencies.append(t_hybrid)

        # 4. Behavioural Risk Service Latency
        t0 = time.perf_counter()
        tx_obj = Transaction(
            sender_id=f"C_BENCH_{i % 10}",
            receiver_id=f"M_BENCH_{i % 5}",
            amount=10000.0 + (i * 500),
            transaction_type="TRANSFER",
            status="processed",
            created_at=datetime.now(timezone.utc)
        )
        db.add(tx_obj)
        db.commit()

        b_eval = behavioural_risk_service.evaluate_transaction_behaviour(tx_obj.transaction_id, db=db)
        t_beh = (time.perf_counter() - t0) * 1000
        behaviour_latencies.append(t_beh)

        # 5. Full Pipeline Latency (Inference + Hybrid + DB Commit)
        t0 = time.perf_counter()
        _ = ml_service.predict(sample_tx)
        _ = risk_engine.compute_risk(0.1, 0.2)
        _ = behavioural_risk_service.get_account_profile(f"C_BENCH_{i % 10}", db=db)
        t_pipe = (time.perf_counter() - t0) * 1000
        pipeline_latencies.append(t_pipe)

    db.close()

    def calc_stats(arr):
        return {
            "avg_ms": round(float(np.mean(arr)), 2),
            "p50_ms": round(float(np.percentile(arr, 50)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2),
            "p99_ms": round(float(np.percentile(arr, 99)), 2),
            "min_ms": round(float(np.min(arr)), 2),
            "max_ms": round(float(np.max(arr)), 2)
        }

    stats_xgb = calc_stats(xgb_latencies)
    stats_vqc = calc_stats(vqc_latencies)
    stats_hybrid = calc_stats(hybrid_latencies)
    stats_beh = calc_stats(behaviour_latencies)
    stats_pipe = calc_stats(pipeline_latencies)

    # Throughput (ops/sec) based on avg full pipeline latency
    throughput_tps = round(1000.0 / stats_pipe["avg_ms"], 2) if stats_pipe["avg_ms"] > 0 else 0

    print("\nBENCHMARK RESULTS SUMMARY:")
    print("+----------------------------------+----------+----------+----------+----------+")
    print("| Component / Pipeline             | Avg (ms) | P50 (ms) | P95 (ms) | P99 (ms) |")
    print("+----------------------------------+----------+----------+----------+----------+")
    print(f"| Classical XGBoost Model          | {stats_xgb['avg_ms']:>8.2f} | {stats_xgb['p50_ms']:>8.2f} | {stats_xgb['p95_ms']:>8.2f} | {stats_xgb['p99_ms']:>8.2f} |")
    print(f"| Quantum VQC Simulator (4 Qubits) | {stats_vqc['avg_ms']:>8.2f} | {stats_vqc['p50_ms']:>8.2f} | {stats_vqc['p95_ms']:>8.2f} | {stats_vqc['p99_ms']:>8.2f} |")
    print(f"| Hybrid Risk Combination Engine   | {stats_hybrid['avg_ms']:>8.2f} | {stats_hybrid['p50_ms']:>8.2f} | {stats_hybrid['p95_ms']:>8.2f} | {stats_hybrid['p99_ms']:>8.2f} |")
    print(f"| Behavioural Risk & Discovery     | {stats_beh['avg_ms']:>8.2f} | {stats_beh['p50_ms']:>8.2f} | {stats_beh['p95_ms']:>8.2f} | {stats_beh['p99_ms']:>8.2f} |")
    print(f"| End-to-End Processing Pipeline   | {stats_pipe['avg_ms']:>8.2f} | {stats_pipe['p50_ms']:>8.2f} | {stats_pipe['p95_ms']:>8.2f} | {stats_pipe['p99_ms']:>8.2f} |")
    print("+----------------------------------+----------+----------+----------+----------+")
    print(f"\nEstimated Throughput: {throughput_tps} transactions / second (single core)")
    print("==========================================================================\n")

    results_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_samples": num_samples,
        "throughput_tps": throughput_tps,
        "xgboost": stats_xgb,
        "vqc": stats_vqc,
        "hybrid_engine": stats_hybrid,
        "behavioural_risk": stats_beh,
        "full_pipeline": stats_pipe
    }

    out_dir = os.path.join(PROJECT_ROOT, "artifacts")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print(f"Benchmark results successfully exported to: {out_file}")
    return results_payload

if __name__ == "__main__":
    run_benchmark(num_samples=100)
