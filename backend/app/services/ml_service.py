import os
import json
import time
import pandas as pd
import xgboost as xgb
from app.ml.features import extract_features

def _get_models_artifacts_dir() -> str:
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../artifacts/models"))
    if os.path.exists(backend_path):
        return backend_path
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../artifacts/models"))

ARTIFACTS_DIR = _get_models_artifacts_dir()


class MLService:
    def __init__(self):
        self.model = None
        self.metadata = None
        self._load_model()
        
    def _load_model(self):
        model_path = os.path.join(ARTIFACTS_DIR, "xgboost_fraud_model.json")
        meta_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
        
        if os.path.exists(model_path) and os.path.exists(meta_path):
            self.model = xgb.XGBClassifier()
            self.model.load_model(model_path)
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)
                
    def get_status(self):
        if not self.model or not self.metadata:
            return {"status": "unavailable", "message": "Model artifacts not found"}
            
        return {
            "status": "available",
            "model_name": self.metadata.get("model_name"),
            "model_version": self.metadata.get("model_version"),
            "training_timestamp": self.metadata.get("training_timestamp"),
            "feature_count": len(self.metadata.get("feature_names", [])),
            "metrics": self.metadata.get("evaluation_metrics", {})
        }
        
    def predict(self, transaction_dict: dict) -> dict:
        if not self.model:
            raise Exception("Model not loaded")
            
        start_time = time.time()
        df = pd.DataFrame([transaction_dict])
        features = extract_features(df)
        
        # XGBoost expects the exact feature order
        if self.metadata and "feature_names" in self.metadata:
            features = features[self.metadata["feature_names"]]
            
        prob = float(self.model.predict_proba(features)[0][1])
        pred_class = int(self.model.predict(features)[0])
        exec_time = (time.time() - start_time) * 1000
        
        return {
            "fraud_probability": prob,
            "predicted_class": pred_class,
            "execution_time_ms": exec_time,
            "model_name": self.metadata.get("model_name", "unknown"),
            "model_version": self.metadata.get("model_version", "unknown")
        }

ml_service = MLService()
