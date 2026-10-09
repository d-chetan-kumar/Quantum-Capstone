import os
import json
import time
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from qiskit_algorithms.optimizers import COBYLA
from qiskit_machine_learning.algorithms.classifiers import VQC
from app.ml.quantum_features import extract_quantum_features

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/PS_20174392719_1491204439457_log.csv")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "../../../artifacts/quantum")

COLS = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud']

def save_circuit(feature_map, ansatz, path, img_path):
    qc = feature_map.compose(ansatz)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(qc.draw(output="text")))
    try:
        qc.draw(output="mpl", filename=img_path)
        print(f"Circuit image saved to {img_path}")
    except Exception as e:
        print("Could not save circuit image:", e)

def train():
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}.")
        return

    size = os.path.getsize(DATA_PATH)
    print(f"Loading dataset from: {os.path.abspath(DATA_PATH)} (Size: {size} bytes)")
    
    header_idx = None
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if "step,type,amount" in line and "log_amount" not in line:
                header_idx = idx
                break
                
    if header_idx is None:
        df = pd.read_csv(DATA_PATH)
    else:
        df = pd.read_csv(DATA_PATH, skiprows=header_idx + 1, header=None, names=COLS)

    print(f"Loaded dataset shape: {df.shape}")
    
    # Chronological Split (Train: 70%, Val: 15%, Test: 15%)
    print("Sorting dataset chronologically by step...")
    df = df.sort_values(by='step')
    
    total_rows = len(df)
    train_idx = int(total_rows * 0.7)
    val_idx = int(total_rows * 0.85)
    
    train_df = df.iloc[:train_idx]
    val_df = df.iloc[train_idx:val_idx]
    test_df = df.iloc[val_idx:]
    
    print("\n--- Full Chronological Splits ---")
    print(f"Train Set: {len(train_df)} rows | Fraud: {train_df['isFraud'].sum()} | Non-Fraud: {len(train_df) - train_df['isFraud'].sum()}")
    print(f"Val Set:   {len(val_df)} rows | Fraud: {val_df['isFraud'].sum()} | Non-Fraud: {len(val_df) - val_df['isFraud'].sum()}")
    print(f"Test Set:  {len(test_df)} rows | Fraud: {test_df['isFraud'].sum()} | Non-Fraud: {len(test_df) - test_df['isFraud'].sum()}")

    # Sampling for VQC computational feasibility
    # Deterministic sampling from each chronological split
    train_fraud = train_df[train_df['isFraud'] == 1].sample(n=min(150, train_df['isFraud'].sum()), random_state=42)
    train_non_fraud = train_df[train_df['isFraud'] == 0].sample(n=150, random_state=42)
    sample_train_df = pd.concat([train_fraud, train_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)

    val_fraud = val_df[val_df['isFraud'] == 1].sample(n=min(50, val_df['isFraud'].sum()), random_state=42)
    val_non_fraud = val_df[val_df['isFraud'] == 0].sample(n=50, random_state=42)
    sample_val_df = pd.concat([val_fraud, val_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)

    test_fraud = test_df[test_df['isFraud'] == 1].sample(n=min(100, test_df['isFraud'].sum()), random_state=42)
    test_non_fraud = test_df[test_df['isFraud'] == 0].sample(n=100, random_state=42)
    sample_test_df = pd.concat([test_fraud, test_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)

    print("\n--- Deterministic VQC Sampled Subsets ---")
    print(f"Train Sampled: {len(sample_train_df)} rows | Fraud: {sample_train_df['isFraud'].sum()} | Non-Fraud: {len(sample_train_df) - sample_train_df['isFraud'].sum()}")
    print(f"Val Sampled:   {len(sample_val_df)} rows | Fraud: {sample_val_df['isFraud'].sum()} | Non-Fraud: {len(sample_val_df) - sample_val_df['isFraud'].sum()}")
    print(f"Test Sampled:  {len(sample_test_df)} rows | Fraud: {sample_test_df['isFraud'].sum()} | Non-Fraud: {len(sample_test_df) - sample_test_df['isFraud'].sum()}")

    X_train = extract_quantum_features(sample_train_df)
    y_train = sample_train_df['isFraud'].values

    X_val = extract_quantum_features(sample_val_df)
    y_val = sample_val_df['isFraud'].values

    X_test = extract_quantum_features(sample_test_df)
    y_test = sample_test_df['isFraud'].values

    print("\nScaling quantum features to [0, pi] range...")
    scaler = MinMaxScaler(feature_range=(0, np.pi))
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    print("\nBuilding 4-Qubit Variational Quantum Classifier (VQC)...")
    num_qubits = 4
    feature_map = ZZFeatureMap(feature_dimension=num_qubits, reps=1)
    ansatz = RealAmplitudes(num_qubits=num_qubits, entanglement='linear', reps=2)
    optimizer = COBYLA(maxiter=60)

    vqc = VQC(
        feature_map=feature_map,
        ansatz=ansatz,
        optimizer=optimizer
    )

    print("Training VQC on quantum simulator...")
    t0 = time.time()
    vqc.fit(X_train_scaled, y_train)
    train_duration = time.time() - t0
    print(f"VQC Training completed in {train_duration:.2f} seconds.")

    print("Evaluating VQC on held-out test set...")
    t1 = time.time()
    y_pred = vqc.predict(X_test_scaled)
    
    if hasattr(vqc, "predict_proba"):
        y_proba_mat = vqc.predict_proba(X_test_scaled)
        y_prob = y_proba_mat[:, 1] if y_proba_mat.ndim == 2 else y_proba_mat
    else:
        y_prob = y_pred.astype(float)
        
    eval_duration = time.time() - t1
    print(f"VQC Evaluation completed in {eval_duration:.2f} seconds.")

    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 0.5
    pr_auc = float(average_precision_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 0.5
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "confusion_matrix": cm,
        "train_duration_seconds": train_duration,
        "eval_duration_seconds": eval_duration
    }

    print("\n================ VQC EVALUATION METRICS ================")
    print(json.dumps(metrics, indent=2))

    print("\nSaving Quantum Artifacts...")
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(ARTIFACTS_DIR, "vqc_model"), exist_ok=True)

    vqc.save(os.path.join(ARTIFACTS_DIR, "vqc_model", "model.vqc"))

    with open(os.path.join(ARTIFACTS_DIR, "quantum_scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)

    save_circuit(
        feature_map, ansatz,
        os.path.join(ARTIFACTS_DIR, "circuit.txt"),
        os.path.join(ARTIFACTS_DIR, "circuit.png")
    )

    metadata = {
        "model_name": "vqc",
        "model_version": "v1.0",
        "number_of_qubits": 4,
        "quantum_features": ["transaction_type", "hour_of_day", "day_of_week", "log_amount"],
        "feature_map": "ZZFeatureMap",
        "ansatz": "RealAmplitudes",
        "repetitions": 2,
        "entanglement": "linear",
        "optimizer": "COBYLA",
        "scaling_range": "[0, pi]",
        "dataset_stats": {
            "total_dataset_rows": total_rows,
            "train_full_rows": len(train_df),
            "val_full_rows": len(val_df),
            "test_full_rows": len(test_df),
            "train_sample_rows": len(sample_train_df),
            "val_sample_rows": len(sample_val_df),
            "test_sample_rows": len(sample_test_df),
            "train_sample_fraud": int(sample_train_df['isFraud'].sum()),
            "val_sample_fraud": int(sample_val_df['isFraud'].sum()),
            "test_sample_fraud": int(sample_test_df['isFraud'].sum())
        },
        "training_timestamp": time.time(),
        "evaluation_metrics": metrics
    }

    with open(os.path.join(ARTIFACTS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(ARTIFACTS_DIR, "evaluation.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nVQC Training and Artifact Generation Complete.")

if __name__ == "__main__":
    train()
