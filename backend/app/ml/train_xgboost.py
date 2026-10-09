import os
import json
import time
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, roc_curve, precision_recall_curve
from app.ml.features import extract_features

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/PS_20174392719_1491204439457_log.csv")
MODEL_ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "../../../artifacts/models")
EVAL_ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "../../../artifacts/evaluations")

COLS = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud']

def train():
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}. Please download PaySim dataset.")
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
        print("Header not found, reading from top...")
        df = pd.read_csv(DATA_PATH)
    else:
        print(f"Skipping {header_idx + 1} lines to bypass header and prepended prompt text...")
        df = pd.read_csv(DATA_PATH, skiprows=header_idx + 1, header=None, names=COLS)

    print(f"Loaded dataset shape: {df.shape}")
    
    # Chronological Split (Train: first 70%, Val: next 15%, Test: last 15%)
    print("Splitting dataset chronologically...")
    df = df.sort_values(by='step')
    
    train_idx = int(len(df) * 0.7)
    val_idx = int(len(df) * 0.85)
    
    train_df = df.iloc[:train_idx]
    val_df = df.iloc[train_idx:val_idx]
    test_df = df.iloc[val_idx:]
    
    print(f"Train Rows: {len(train_df)} / Fraud: {train_df['isFraud'].sum()}")
    print(f"Validation Rows: {len(val_df)} / Fraud: {val_df['isFraud'].sum()}")
    print(f"Test Rows: {len(test_df)} / Fraud: {test_df['isFraud'].sum()}")

    print("Feature Engineering...")
    X_train = extract_features(train_df)
    y_train = train_df['isFraud']
    
    X_val = extract_features(val_df)
    y_val = val_df['isFraud']
    
    X_test = extract_features(test_df)
    y_test = test_df['isFraud']
    
    scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1]) if len(y_train[y_train == 1]) > 0 else 1
    print(f"Calculated scale_pos_weight (from Train split only): {scale_pos_weight:.4f}")

    print("Training XGBoost...")
    params = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'scale_pos_weight': scale_pos_weight
    }
    
    t0 = time.time()
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=10)
    train_duration = time.time() - t0
    print(f"Training completed in {train_duration:.2f} seconds.")

    print("Evaluating on Test Set...")
    t1 = time.time()
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    eval_duration = time.time() - t1
    print(f"Evaluation completed in {eval_duration:.2f} seconds.")

    precision = float(precision_score(y_test, y_pred))
    recall = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, y_prob)

    # Feature Importance
    importance_map = model.get_booster().get_score(importance_type='weight')
    # Map feature names
    feature_names = X_train.columns.tolist()
    feature_importance = {}
    for col in feature_names:
        feature_importance[col] = importance_map.get(col, 0)

    metrics = {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "confusion_matrix": cm,
        "feature_importance": feature_importance,
        "train_duration_seconds": train_duration,
        "eval_duration_seconds": eval_duration
    }
    
    print("\n================ EVALUATION METRICS ================")
    print(json.dumps(metrics, indent=2))
    
    os.makedirs(MODEL_ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(EVAL_ARTIFACTS_DIR, exist_ok=True)

    # Save model
    model_path = os.path.join(MODEL_ARTIFACTS_DIR, "xgboost_fraud_model.json")
    model.save_model(model_path)
    
    metadata = {
        "model_name": "xgboost_paysim",
        "model_version": "v1.0",
        "training_timestamp": time.time(),
        "feature_names": feature_names,
        "hyperparameters": params,
        "evaluation_metrics": metrics,
        "dataset_stats": {
            "train_rows": len(X_train),
            "val_rows": len(X_val),
            "test_rows": len(X_test),
            "train_fraud": int(y_train.sum()),
            "val_fraud": int(y_val.sum()),
            "test_fraud": int(y_test.sum())
        }
    }
    
    with open(os.path.join(MODEL_ARTIFACTS_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Save evaluation artifacts
    with open(os.path.join(EVAL_ARTIFACTS_DIR, "xgboost_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(EVAL_ARTIFACTS_DIR, "confusion_matrix.json"), "w") as f:
        json.dump({
            "tn": cm[0][0], "fp": cm[0][1],
            "fn": cm[1][0], "tp": cm[1][1],
            "matrix": cm
        }, f, indent=2)

    # Subsample curves to max 500 points for efficient visualization
    step_fpr = max(1, len(fpr) // 500)
    with open(os.path.join(EVAL_ARTIFACTS_DIR, "roc_curve.json"), "w") as f:
        json.dump({
            "fpr": fpr[::step_fpr].tolist(),
            "tpr": tpr[::step_fpr].tolist(),
            "roc_auc": roc_auc
        }, f, indent=2)

    step_pr = max(1, len(prec_curve) // 500)
    with open(os.path.join(EVAL_ARTIFACTS_DIR, "precision_recall_curve.json"), "w") as f:
        json.dump({
            "precision": prec_curve[::step_pr].tolist(),
            "recall": rec_curve[::step_pr].tolist(),
            "pr_auc": pr_auc
        }, f, indent=2)

    with open(os.path.join(EVAL_ARTIFACTS_DIR, "feature_importance.json"), "w") as f:
        json.dump(feature_importance, f, indent=2)
        
    print("\nTraining and Artifact Generation Complete.")

if __name__ == "__main__":
    train()

