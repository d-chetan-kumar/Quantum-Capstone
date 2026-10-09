import os
import json
import time
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
from qiskit_machine_learning.algorithms.classifiers import VQC

from app.ml.features import extract_features
from app.ml.quantum_features import extract_quantum_features

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/PS_20174392719_1491204439457_log.csv")
XGB_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../../artifacts/models/xgboost_fraud_model.json")
VQC_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../../artifacts/quantum/vqc_model/model.vqc")
VQC_SCALER_PATH = os.path.join(os.path.dirname(__file__), "../../../artifacts/quantum/quantum_scaler.pkl")
HYBRID_DIR = os.path.join(os.path.dirname(__file__), "../../../artifacts/hybrid")

COLS = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud']

def evaluate_predictions(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    pr_auc = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    cm = confusion_matrix(y_true, y_pred).tolist()
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "confusion_matrix": cm
    }

def run_hybrid_experiment():
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}.")
        return

    print("Loading models...")
    xgb_model = xgb.XGBClassifier()
    xgb_model.load_model(XGB_MODEL_PATH)

    vqc_model = VQC.load(VQC_MODEL_PATH)
    with open(VQC_SCALER_PATH, "rb") as f:
        vqc_scaler = pickle.load(f)

    print("Loading PaySim dataset...")
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

    df = df.sort_values(by='step')
    total_rows = len(df)
    train_idx = int(total_rows * 0.7)
    val_idx = int(total_rows * 0.85)

    val_df = df.iloc[train_idx:val_idx]
    test_df = df.iloc[val_idx:]

    print("\n================ 1. COMMON VALIDATION SUBSET ================")
    # Deterministic common validation sample (100 rows: 50 fraud, 50 non-fraud)
    val_fraud = val_df[val_df['isFraud'] == 1].sample(n=min(50, val_df['isFraud'].sum()), random_state=42)
    val_non_fraud = val_df[val_df['isFraud'] == 0].sample(n=50, random_state=42)
    common_val_df = pd.concat([val_fraud, val_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)

    y_val = common_val_df['isFraud'].values

    # Classical Features & Prediction for Validation
    X_val_xgb = extract_features(common_val_df)
    xgb_val_prob = xgb_model.predict_proba(X_val_xgb)[:, 1]

    # Quantum Features & Prediction for Validation
    X_val_vqc = extract_quantum_features(common_val_df)
    X_val_vqc_scaled = vqc_scaler.transform(X_val_vqc)
    vqc_val_prob_mat = vqc_model.predict_proba(X_val_vqc_scaled)
    vqc_val_prob = vqc_val_prob_mat[:, 1] if vqc_val_prob_mat.ndim == 2 else vqc_val_prob_mat.ravel()

    print(f"Common Val Subset: {len(common_val_df)} rows (Fraud: {y_val.sum()}, Non-Fraud: {len(y_val) - y_val.sum()})")

    print("\n================ 2. HYBRID WEIGHT GRID SEARCH ================")
    best_weight_xgb = 0.5
    best_weight_vqc = 0.5
    best_val_f1 = -1.0
    best_val_metrics = None

    search_results = []
    # Grid search from 0.0 to 1.0 with step 0.05
    for w_xgb_int in range(0, 21):
        w_xgb = round(w_xgb_int * 0.05, 2)
        w_vqc = round(1.0 - w_xgb, 2)

        hybrid_val_prob = w_xgb * xgb_val_prob + w_vqc * vqc_val_prob
        m = evaluate_predictions(y_val, hybrid_val_prob)
        m["w_xgb"] = w_xgb
        m["w_vqc"] = w_vqc
        search_results.append(m)

        if m["f1_score"] > best_val_f1:
            best_val_f1 = m["f1_score"]
            best_weight_xgb = w_xgb
            best_weight_vqc = w_vqc
            best_val_metrics = m

    print(f"Optimal Weight Selection on Validation Set (Metric: F1-Score):")
    print(f"-> Selected XGBoost Weight: {best_weight_xgb}")
    print(f"-> Selected VQC Weight:     {best_weight_vqc}")
    print(f"-> Validation F1 Score:     {best_val_f1:.4f}")

    print("\n================ 3. COMMON TEST SUBSET EVALUATION ================")
    # Deterministic common test sample (200 rows: 100 fraud, 100 non-fraud)
    test_fraud = test_df[test_df['isFraud'] == 1].sample(n=min(100, test_df['isFraud'].sum()), random_state=42)
    test_non_fraud = test_df[test_df['isFraud'] == 0].sample(n=100, random_state=42)
    common_test_df = pd.concat([test_fraud, test_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)

    y_test = common_test_df['isFraud'].values

    # Predictions on Common Test Subset
    X_test_xgb = extract_features(common_test_df)
    xgb_test_prob = xgb_model.predict_proba(X_test_xgb)[:, 1]

    X_test_vqc = extract_quantum_features(common_test_df)
    X_test_vqc_scaled = vqc_scaler.transform(X_test_vqc)
    vqc_test_prob_mat = vqc_model.predict_proba(X_test_vqc_scaled)
    vqc_test_prob = vqc_test_prob_mat[:, 1] if vqc_test_prob_mat.ndim == 2 else vqc_test_prob_mat.ravel()

    hybrid_test_prob = best_weight_xgb * xgb_test_prob + best_weight_vqc * vqc_test_prob

    xgb_metrics = evaluate_predictions(y_test, xgb_test_prob)
    vqc_metrics = evaluate_predictions(y_test, vqc_test_prob)
    hybrid_metrics = evaluate_predictions(y_test, hybrid_test_prob)

    print("\n--- Comparative Evaluation on Common Test Subset ---")
    print(f"XGBoost  -> Precision: {xgb_metrics['precision']:.4f} | Recall: {xgb_metrics['recall']:.4f} | F1: {xgb_metrics['f1_score']:.4f} | ROC-AUC: {xgb_metrics['roc_auc']:.4f}")
    print(f"VQC      -> Precision: {vqc_metrics['precision']:.4f} | Recall: {vqc_metrics['recall']:.4f} | F1: {vqc_metrics['f1_score']:.4f} | ROC-AUC: {vqc_metrics['roc_auc']:.4f}")
    print(f"Hybrid   -> Precision: {hybrid_metrics['precision']:.4f} | Recall: {hybrid_metrics['recall']:.4f} | F1: {hybrid_metrics['f1_score']:.4f} | ROC-AUC: {hybrid_metrics['roc_auc']:.4f}")

    print("\n================ 4. SAVING HYBRID ARTIFACTS ================")
    os.makedirs(HYBRID_DIR, exist_ok=True)

    hybrid_config = {
        "model_name": "hybrid_xgb_vqc",
        "model_version": "v1.0",
        "timestamp": time.time(),
        "weights": {
            "xgboost_weight": best_weight_xgb,
            "vqc_weight": best_weight_vqc
        },
        "selection_strategy": {
            "metric": "f1_score",
            "validation_sample_count": len(common_val_df),
            "validation_fraud_count": int(y_val.sum()),
            "validation_non_fraud_count": int(len(y_val) - y_val.sum()),
            "best_validation_f1": best_val_f1
        }
    }

    risk_config = {
        "version": "v1.0",
        "thresholds": {
            "safe_max": 0.30,
            "review_max": 0.70,
            "alert_min": 0.70
        },
        "labels": {
            "SAFE": "Safe transaction - low risk",
            "REVIEW": "Manual review required - moderate risk",
            "ALERT": "High risk fraud alert triggered"
        }
    }

    evaluation_report = {
        "population": "Common Test Subset",
        "sample_count": len(common_test_df),
        "fraud_count": int(y_test.sum()),
        "non_fraud_count": int(len(y_test) - y_test.sum()),
        "weights": {
            "xgboost": best_weight_xgb,
            "vqc": best_weight_vqc
        },
        "models": {
            "xgboost": xgb_metrics,
            "vqc": vqc_metrics,
            "hybrid": hybrid_metrics
        }
    }

    with open(os.path.join(HYBRID_DIR, "hybrid_config.json"), "w") as f:
        json.dump(hybrid_config, f, indent=2)

    with open(os.path.join(HYBRID_DIR, "risk_config.json"), "w") as f:
        json.dump(risk_config, f, indent=2)

    with open(os.path.join(HYBRID_DIR, "hybrid_evaluation.json"), "w") as f:
        json.dump(evaluation_report, f, indent=2)

    print("Hybrid Experiment and Artifact Generation Complete.")

if __name__ == "__main__":
    run_hybrid_experiment()
