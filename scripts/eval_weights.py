import os
import sys
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from qiskit_machine_learning.algorithms.classifiers import VQC

# Ensure backend in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ml.features import extract_features
from app.ml.quantum_features import extract_quantum_features

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "PS_20174392719_1491204439457_log.csv")
XGB_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "models", "xgboost_fraud_model.json")
VQC_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "quantum", "vqc_model", "model.vqc")
VQC_SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "quantum", "quantum_scaler.pkl")

print("Loading models...")
xgb_model = xgb.XGBClassifier()
xgb_model.load_model(XGB_MODEL_PATH)

vqc_model = VQC.load(VQC_MODEL_PATH)
with open(VQC_SCALER_PATH, "rb") as f:
    vqc_scaler = pickle.load(f)

COLS = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud']

print("Loading dataset...")
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
val_idx = int(len(df) * 0.85)
test_df = df.iloc[val_idx:]

test_fraud = test_df[test_df["isFraud"] == 1].sample(n=min(100, test_df["isFraud"].sum()), random_state=42)
test_non_fraud = test_df[test_df["isFraud"] == 0].sample(n=100, random_state=42)
common_test_df = pd.concat([test_fraud, test_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)
y_test = common_test_df["isFraud"].values

print("Extracting features & evaluating models on common test subset...")
X_test_xgb = extract_features(common_test_df)
xgb_prob = xgb_model.predict_proba(X_test_xgb)[:, 1]

X_test_vqc = extract_quantum_features(common_test_df)
X_test_vqc_scaled = vqc_scaler.transform(X_test_vqc)
vqc_prob_mat = vqc_model.predict_proba(X_test_vqc_scaled)
vqc_prob = vqc_prob_mat[:, 1] if vqc_prob_mat.ndim == 2 else vqc_prob_mat.ravel()

print("\n--- Model Baseline Metrics ---")
for name, prob in [("XGBoost Alone (1.0 / 0.0)", xgb_prob), ("VQC Alone (0.0 / 1.0)", vqc_prob)]:
    y_p = (prob >= 0.5).astype(int)
    cm = confusion_matrix(y_test, y_p)
    print(f"{name}:")
    print(f"  Precision: {precision_score(y_test, y_p):.4f}")
    print(f"  Recall:    {recall_score(y_test, y_p):.4f}")
    print(f"  F1-Score:  {f1_score(y_test, y_p):.4f}")
    print(f"  ROC-AUC:   {roc_auc_score(y_test, prob):.4f}")
    print(f"  Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")

print("\n--- Weight Sweep Analysis (Threshold = 0.5) ---")
print(f"{'w_xgb':>6} | {'w_vqc':>6} | {'Precision':>9} | {'Recall':>8} | {'F1-Score':>8} | {'ROC-AUC':>8} | {'TP':>3} | {'FN':>3} | Notes")
print("-" * 75)

for w_xgb_i in range(0, 21):
    w_xgb = round(w_xgb_i * 0.05, 2)
    w_vqc = round(1.0 - w_xgb, 2)
    p_hyb = w_xgb * xgb_prob + w_vqc * vqc_prob
    y_pred = (p_hyb >= 0.5).astype(int)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, p_hyb)
    cm = confusion_matrix(y_test, y_pred)
    tp = cm[1, 1]
    fn = cm[1, 0]
    if abs(w_xgb - 0.50) < 1e-4:
        note = "<-- ACTIVE PRODUCTION (50% XGB / 50% VQC)"
    elif abs(w_xgb - 0.30) < 1e-4:
        note = "<-- HISTORICAL BASELINE (30% XGB / 70% VQC)"
    elif abs(w_xgb - 0.70) < 1e-4:
        note = "<-- ALTERNATIVE CANDIDATE (70% XGB / 30% VQC)"
    print(f"{w_xgb:6.2f} | {w_vqc:6.2f} | {prec:9.4f} | {rec:8.4f} | {f1:8.4f} | {auc:8.4f} | {tp:3d} | {fn:3d} | {note}")
