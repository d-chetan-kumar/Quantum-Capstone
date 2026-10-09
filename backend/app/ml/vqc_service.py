import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from qiskit_algorithms.optimizers import COBYLA
from qiskit_machine_learning.algorithms.classifiers import VQC
from app.ml.quantum_features import extract_quantum_features

def _get_quantum_artifacts_dir() -> str:
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../artifacts/quantum"))
    if os.path.exists(backend_path):
        return backend_path
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../artifacts/quantum"))

ARTIFACTS_DIR = _get_quantum_artifacts_dir()
VQC_MODEL_DIR = os.path.join(ARTIFACTS_DIR, "vqc_model")
VQC_MODEL_PATH = os.path.join(VQC_MODEL_DIR, "model.vqc")
WEIGHTS_PATH = os.path.join(VQC_MODEL_DIR, "weights.json")
SCALER_PATH = os.path.join(ARTIFACTS_DIR, "quantum_scaler.pkl")
METADATA_PATH = os.path.join(ARTIFACTS_DIR, "metadata.json")


class VQCService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.metadata = None
        self.status = "uninitialized"
        self.diagnostic_reason = "Model service initialized."
        self._load_model()

    def _load_model(self):
        # 1. Check artifact existence
        if not (os.path.exists(VQC_MODEL_PATH) or os.path.exists(WEIGHTS_PATH)) or not os.path.exists(SCALER_PATH) or not os.path.exists(METADATA_PATH):
            self.status = "missing_artifacts"
            self.diagnostic_reason = "Required model (model.vqc/weights.json), scaler (quantum_scaler.pkl), or metadata (metadata.json) artifacts missing."
            self.model = None
            return

        # 2. Load metadata and scaler
        try:
            with open(SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        except Exception as e:
            self.status = "loading_failed"
            self.diagnostic_reason = f"Failed to load scaler or metadata artifact: {str(e)}"
            self.model = None
            return

        # 3. Load VQC weights & reconstruct VQC classifier instance
        weights = None
        if os.path.exists(WEIGHTS_PATH):
            try:
                with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
                    w_data = json.load(f)
                    weights = np.array(w_data["weights"], dtype=np.float64)
            except Exception as e:
                print(f"Could not load sidecar weights.json: {e}")

        if weights is None and os.path.exists(VQC_MODEL_PATH):
            try:
                self.model = VQC.load(VQC_MODEL_PATH)
            except Exception as e:
                print(f"Standard VQC.load failed (Qiskit version incompatibility): {e}. Recovering trained weights from binary...")
                try:
                    import pickletools
                    with open(VQC_MODEL_PATH, "rb") as f:
                        content = f.read()
                    ops = list(pickletools.genops(content))
                    for op, arg, pos in ops:
                        if 'BYTES' in op.name and len(arg) == 96:
                            weights = np.frombuffer(arg, dtype=np.float64)
                            break
                except Exception as ex:
                    print(f"Failed to recover weights from model.vqc: {ex}")

        if weights is not None:
            try:
                # Save sidecar weights.json if not present
                if not os.path.exists(WEIGHTS_PATH):
                    try:
                        with open(WEIGHTS_PATH, "w", encoding="utf-8") as f:
                            json.dump({"weights": weights.tolist()}, f, indent=2)
                    except Exception:
                        pass

                num_qubits = self.metadata.get("number_of_qubits", 4)
                reps = self.metadata.get("repetitions", 2)
                entanglement = self.metadata.get("entanglement", "linear")

                fm = ZZFeatureMap(feature_dimension=num_qubits, reps=1)
                ans = RealAmplitudes(num_qubits=num_qubits, entanglement=entanglement, reps=reps)
                vqc_inst = VQC(feature_map=fm, ansatz=ans, optimizer=COBYLA(maxiter=14))
                # Dry fit to initialize internals
                vqc_inst.fit(np.zeros((2, num_qubits)), np.array([0, 1]))
                vqc_inst._fit_result.x = weights
                self.model = vqc_inst
            except Exception as e:
                self.status = "loading_failed"
                self.diagnostic_reason = f"Failed to instantiate VQC model with weights: {str(e)}"
                self.model = None
                return

        if self.model is None:
            self.status = "loading_failed"
            self.diagnostic_reason = "VQC model could not be loaded or deserialized."
            return

        # 4. Perform dry-run prediction test to guarantee inference readiness
        try:
            sample_tx = {'step': 1, 'type': 'TRANSFER', 'amount': 100.0, 'nameOrig': 'C1', 'oldbalanceOrg': 100.0, 'newbalanceOrig': 0.0, 'nameDest': 'M1', 'oldbalanceDest': 0.0, 'newbalanceDest': 0.0}
            df = pd.DataFrame([sample_tx])
            X_feat = extract_quantum_features(df)
            X_scaled = self.scaler.transform(X_feat)
            prob = self.model.predict_proba(X_scaled)
            pred = self.model.predict(X_scaled)
            if not np.isfinite(prob).all():
                raise ValueError("Non-finite probability returned during dry-run inference")
            self.status = "available"
            self.diagnostic_reason = "Trained and inference-ready."
        except Exception as e:
            self.status = "inference_unavailable"
            self.diagnostic_reason = f"VQC model loaded but failed dry-run inference: {str(e)}"
            self.model = None

    def is_available(self) -> bool:
        return self.status == "available" and self.model is not None and self.scaler is not None

    def predict(self, transaction_data: Dict[str, Any]) -> Tuple[float, int]:
        if not self.is_available():
            raise RuntimeError(f"VQC Model is not available: {self.diagnostic_reason}")

        df = pd.DataFrame([transaction_data])
        X_feat = extract_quantum_features(df)
        X_scaled = self.scaler.transform(X_feat)
        X_scaled = np.asarray(X_scaled, dtype=np.float64)
        if X_scaled.ndim == 1:
            X_scaled = X_scaled.reshape(1, -1)
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1.0, neginf=0.0)

        y_pred = np.asarray(self.model.predict(X_scaled)).ravel()
        pred_class = int(y_pred[0])

        if hasattr(self.model, "predict_proba"):
            y_prob = np.asarray(self.model.predict_proba(X_scaled))
            if y_prob.ndim == 2 and y_prob.shape[1] >= 2:
                prob = float(y_prob[0, 1])
            else:
                prob = float(y_prob.ravel()[0])
        else:
            prob = float(pred_class)

        prob = min(max(float(prob), 0.0), 1.0)
        return prob, pred_class


    def get_metadata(self) -> Dict[str, Any]:
        meta = self.metadata.copy() if self.metadata else {}
        meta["status"] = self.status
        meta["available"] = self.is_available()
        meta["diagnostic_reason"] = self.diagnostic_reason
        return meta

vqc_service = VQCService()
