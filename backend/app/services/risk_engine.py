import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.ml_service import ml_service
from app.ml.vqc_service import vqc_service

HYBRID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../artifacts/hybrid"))
HYBRID_CONFIG_PATH = os.path.join(HYBRID_DIR, "hybrid_config.json")
RISK_CONFIG_PATH = os.path.join(HYBRID_DIR, "risk_config.json")
EVALUATION_PATH = os.path.join(HYBRID_DIR, "hybrid_evaluation.json")

class RiskEngine:
    def __init__(self):
        self.xgb_weight = 0.3
        self.vqc_weight = 0.7
        self.safe_max = 0.30
        self.review_max = 0.70
        self.alert_min = 0.70
        self._load_config()

    def _load_config(self):
        if os.path.exists(HYBRID_CONFIG_PATH):
            try:
                with open(HYBRID_CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    weights = cfg.get("weights", {})
                    self.xgb_weight = float(weights.get("xgboost_weight", 0.3))
                    self.vqc_weight = float(weights.get("vqc_weight", 0.7))
            except Exception as e:
                print(f"Failed to load hybrid config: {e}")

        if os.path.exists(RISK_CONFIG_PATH):
            try:
                with open(RISK_CONFIG_PATH, "r", encoding="utf-8") as f:
                    rcfg = json.load(f)
                    thresh = rcfg.get("thresholds", {})
                    self.safe_max = float(thresh.get("safe_max", 0.30))
                    self.review_max = float(thresh.get("review_max", 0.70))
                    self.alert_min = float(thresh.get("alert_min", 0.70))
            except Exception as e:
                print(f"Failed to load risk config: {e}")

    def get_config(self) -> Dict[str, Any]:
        return {
            "xgboost_weight": self.xgb_weight,
            "vqc_weight": self.vqc_weight,
            "thresholds": {
                "safe_max": self.safe_max,
                "review_max": self.review_max,
                "alert_min": self.alert_min
            }
        }

    def get_evaluation(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(EVALUATION_PATH):
            try:
                with open(EVALUATION_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load hybrid evaluation: {e}")
        return None

    def compute_risk(self, classical_prob: float, quantum_prob: float) -> Dict[str, Any]:
        hybrid_prob = float(self.xgb_weight * classical_prob + self.vqc_weight * quantum_prob)
        hybrid_prob = min(max(hybrid_prob, 0.0), 1.0) # Clamp 0 to 1

        if hybrid_prob < self.safe_max:
            risk_level = "SAFE"
        elif hybrid_prob < self.review_max:
            risk_level = "REVIEW"
        else:
            risk_level = "ALERT"

        return {
            "hybrid_probability": hybrid_prob,
            "risk_level": risk_level,
            "xgboost_weight": self.xgb_weight,
            "vqc_weight": self.vqc_weight
        }

    def evaluate_transaction(self, transaction_dict: Dict[str, Any], transaction_id: str, db=None) -> Dict[str, Any]:
        # 1. Classical XGBoost Prediction
        xgb_res = ml_service.predict(transaction_dict)
        p_xgb = float(xgb_res.get("fraud_probability", 0.0))

        # 2. Quantum VQC Prediction
        if vqc_service.is_available():
            p_vqc, _ = vqc_service.predict(transaction_dict)
            p_vqc = float(p_vqc)
        else:
            p_vqc = p_xgb # Fallback if VQC is unavailable

        # 3. Hybrid Calculation
        risk_res = self.compute_risk(p_xgb, p_vqc)
        
        now_str = datetime.now(timezone.utc).isoformat()

        output = {
            "transaction_id": transaction_id,
            "classical_probability": p_xgb,
            "quantum_probability": p_vqc,
            "hybrid_probability": risk_res["hybrid_probability"],
            "risk_level": risk_res["risk_level"],
            "xgboost_weight": risk_res["xgboost_weight"],
            "vqc_weight": risk_res["vqc_weight"],
            "created_at": now_str,
            "model_versions": {
                "xgboost": "v1.0",
                "vqc": "v1.0",
                "hybrid": "v1.0"
            }
        }

        # 4. Create database Alert if risk_level == 'ALERT' and db session provided
        if risk_res["risk_level"] == "ALERT" and db is not None:
            try:
                from app.models.alert import FraudAlert
                alert_obj = FraudAlert(
                    transaction_id=transaction_id,
                    alert_reason=f"High hybrid fraud probability ({risk_res['hybrid_probability']:.4f})",
                    resolved=False,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(alert_obj)
                db.commit()
            except Exception as e:
                print(f"Alert persistence skipped: {e}")

        return output

risk_engine = RiskEngine()
