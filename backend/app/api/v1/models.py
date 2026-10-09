from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.services.ml_service import ml_service
import os
import json

router = APIRouter()

@router.get("/xgboost/status")
def get_model_status():
    return ml_service.get_status()

# --- VQC Endpoints ---
from app.ml.vqc_service import vqc_service

@router.get("/vqc/status")
def get_vqc_status():
    return vqc_service.get_metadata()

def _get_quantum_artifacts_dir() -> str:
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../artifacts/quantum"))
    if os.path.exists(backend_path):
        return backend_path
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../artifacts/quantum"))

@router.get("/vqc/evaluation")
def get_vqc_evaluation():
    ARTIFACTS_DIR = _get_quantum_artifacts_dir()
    eval_path = os.path.join(ARTIFACTS_DIR, "evaluation.json")
    if not os.path.exists(eval_path):
        raise HTTPException(status_code=404, detail="Evaluation not available.")
    with open(eval_path, "r") as f:
        return json.load(f)

@router.get("/vqc/circuit", response_class=PlainTextResponse)
def get_vqc_circuit():
    ARTIFACTS_DIR = _get_quantum_artifacts_dir()
    circuit_path = os.path.join(ARTIFACTS_DIR, "circuit.txt")
    if not os.path.exists(circuit_path):
        raise HTTPException(status_code=404, detail="Circuit not available.")
    with open(circuit_path, "r", encoding="utf-8") as f:
        return f.read()

from fastapi.responses import FileResponse, Response
import io

@router.get("/vqc/circuit/image")
def get_vqc_circuit_image(dpi: int = 150):
    ARTIFACTS_DIR = _get_quantum_artifacts_dir()
    img_path = os.path.join(ARTIFACTS_DIR, "circuit.png")

    try:
        import matplotlib
        matplotlib.use("Agg")
        from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
        fm = ZZFeatureMap(4, reps=1)
        ans = RealAmplitudes(4, entanglement='linear', reps=2)
        qc = fm.compose(ans)
        fig = qc.draw(output="mpl")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=min(max(dpi, 100), 300))
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        if os.path.exists(img_path):
            return FileResponse(img_path, media_type="image/png")
        raise HTTPException(status_code=500, detail=f"Failed to render circuit image: {str(e)}")

@router.get("/vqc/circuit/info")
def get_vqc_circuit_info():
    is_trained = vqc_service.is_available()
    return {
        "is_trained": is_trained,
        "circuit_type": "Trained VQC Model Circuit" if is_trained else "Configured Architecture Diagram",
        "num_qubits": 4,
        "features": [
            {"qubit": "q0", "feature": "transaction_type", "description": "Encoded payment type"},
            {"qubit": "q1", "feature": "hour_of_day", "description": "Hour derived from step/timestamp"},
            {"qubit": "q2", "feature": "day_of_week", "description": "Day of week temporal index"},
            {"qubit": "q3", "feature": "log_amount", "description": "Natural log of payment amount"}
        ],
        "feature_map": {
            "name": "ZZFeatureMap",
            "reps": 1,
            "dimension": 4,
            "entanglement": "full"
        },
        "ansatz": {
            "name": "RealAmplitudes",
            "reps": 2,
            "entanglement": "linear",
            "num_parameters": 12
        }
    }

# --- Hybrid Risk Engine Endpoints ---
from app.services.risk_engine import risk_engine

@router.get("/hybrid/status")
def get_hybrid_status():
    return risk_engine.get_config()

@router.get("/hybrid/evaluation")
def get_hybrid_evaluation():
    eval_data = risk_engine.get_evaluation()
    if not eval_data:
        raise HTTPException(status_code=404, detail="Hybrid evaluation not available.")
    return eval_data
