import os
import sys
import pickle
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
from qiskit_machine_learning.algorithms.classifiers import VQC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ml.features import extract_features
from app.ml.quantum_features import extract_quantum_features

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "PS_20174392719_1491204439457_log.csv")
XGB_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "models", "xgboost_fraud_model.json")
VQC_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "quantum", "vqc_model", "model.vqc")
VQC_SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "quantum", "quantum_scaler.pkl")

COLS = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud']

print("Loading models and scalers...")
xgb_model = xgb.XGBClassifier()
xgb_model.load_model(XGB_MODEL_PATH)

vqc_model = VQC.load(VQC_MODEL_PATH)
with open(VQC_SCALER_PATH, "rb") as f:
    vqc_scaler = pickle.load(f)

print("Loading PaySim dataset chronologically...")
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

df = df.sort_values(by="step")
total_rows = len(df)
train_idx = int(total_rows * 0.70)
val_idx = int(total_rows * 0.85)

val_df = df.iloc[train_idx:val_idx]
test_df = df.iloc[val_idx:]

# Common Validation Subset (Deterministic 100 rows: 50 fraud, 50 non-fraud)
val_fraud = val_df[val_df['isFraud'] == 1].sample(n=min(50, val_df['isFraud'].sum()), random_state=42)
val_non_fraud = val_df[val_df['isFraud'] == 0].sample(n=50, random_state=42)
common_val_df = pd.concat([val_fraud, val_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)
y_val = common_val_df['isFraud'].values

# Feature Extraction & Model Inference on Validation Subset
X_val_xgb = extract_features(common_val_df)
xgb_val_prob = xgb_model.predict_proba(X_val_xgb)[:, 1]

X_val_vqc = extract_quantum_features(common_val_df)
X_val_vqc_scaled = vqc_scaler.transform(X_val_vqc)
vqc_val_prob_mat = vqc_model.predict_proba(X_val_vqc_scaled)
vqc_val_prob = vqc_val_prob_mat[:, 1] if vqc_val_prob_mat.ndim == 2 else vqc_val_prob_mat.ravel()

# Common Test Subset (Deterministic 200 rows: 100 fraud, 100 non-fraud)
test_fraud = test_df[test_df['isFraud'] == 1].sample(n=min(100, test_df['isFraud'].sum()), random_state=42)
test_non_fraud = test_df[test_df['isFraud'] == 0].sample(n=100, random_state=42)
common_test_df = pd.concat([test_fraud, test_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)
y_test = common_test_df['isFraud'].values

X_test_xgb = extract_features(common_test_df)
xgb_test_prob = xgb_model.predict_proba(X_test_xgb)[:, 1]

X_test_vqc = extract_quantum_features(common_test_df)
X_test_vqc_scaled = vqc_scaler.transform(X_test_vqc)
vqc_test_prob_mat = vqc_model.predict_proba(X_test_vqc_scaled)
vqc_test_prob = vqc_test_prob_mat[:, 1] if vqc_test_prob_mat.ndim == 2 else vqc_test_prob_mat.ravel()

configs = [
    ("30% XGB + 70% VQC (Historical Baseline)", 0.30, 0.70),
    ("50% XGB + 50% VQC (Active Production)", 0.50, 0.50),
    ("70% XGB + 30% VQC (Alternative Candidate)", 0.70, 0.30),
]

def evaluate(y_true, prob, name):
    pred = (prob >= 0.50).astype(int)
    cm = confusion_matrix(y_true, pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    prec = float(precision_score(y_true, pred, zero_division=0))
    rec = float(recall_score(y_true, pred, zero_division=0))
    f1 = float(f1_score(y_true, pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, prob))
    pr_auc = float(average_precision_score(y_true, prob))
    return {
        "name": name,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "fpr": fpr,
        "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}
    }

print("\n" + "="*80)
print("1. VALIDATION SET EVALUATION (Used for Model Selection — 100 rows, 50F / 50NF)")
print("="*80)

val_results = {}
for name, w_xgb, w_vqc in configs:
    p_hyb = w_xgb * xgb_val_prob + w_vqc * vqc_val_prob
    res = evaluate(y_val, p_hyb, name)
    val_results[name] = res
    print(f"\nConfiguration: {name}")
    print(f"  Precision: {res['precision']:.4f}")
    print(f"  Recall:    {res['recall']:.4f}")
    print(f"  F1-Score:  {res['f1_score']:.4f}")
    print(f"  ROC-AUC:   {res['roc_auc']:.4f}")
    print(f"  PR-AUC:    {res['pr_auc']:.4f}")
    print(f"  FPR:       {res['fpr']:.4f}")
    print(f"  CM:        TN={res['confusion_matrix']['TN']}, FP={res['confusion_matrix']['FP']}, FN={res['confusion_matrix']['FN']}, TP={res['confusion_matrix']['TP']}")

print("\n" + "="*80)
print("2. HELD-OUT TEST SET EVALUATION (Unbiased Benchmark — 200 rows, 100F / 100NF)")
print("="*80)

test_results = {}
for name, w_xgb, w_vqc in configs:
    p_hyb = w_xgb * xgb_test_prob + w_vqc * vqc_test_prob
    res = evaluate(y_test, p_hyb, name)
    test_results[name] = res
    print(f"\nConfiguration: {name}")
    print(f"  Precision: {res['precision']:.4f}")
    print(f"  Recall:    {res['recall']:.4f}")
    print(f"  F1-Score:  {res['f1_score']:.4f}")
    print(f"  ROC-AUC:   {res['roc_auc']:.4f}")
    print(f"  PR-AUC:    {res['pr_auc']:.4f}")
    print(f"  FPR:       {res['fpr']:.4f}")
    print(f"  CM:        TN={res['confusion_matrix']['TN']}, FP={res['confusion_matrix']['FP']}, FN={res['confusion_matrix']['FN']}, TP={res['confusion_matrix']['TP']}")

# Also save to JSON
eval_out = {
    "validation_set": val_results,
    "test_set": test_results
}
out_path = os.path.join(os.path.dirname(__file__), "..", "artifacts", "hybrid", "weight_comparison_audit.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(eval_out, f, indent=2)
print(f"\nResults exported to: {out_path}")
