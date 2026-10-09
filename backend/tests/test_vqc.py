import pytest
import numpy as np
import pandas as pd
from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from app.ml.quantum_features import extract_quantum_features
from app.ml.vqc_service import vqc_service

def test_extract_quantum_features():
    df = pd.DataFrame([{
        "step": 36, # day 1 (36 // 24 = 1), hour 12 (36 % 24 = 12)
        "type": "TRANSFER",
        "amount": 100.0
    }])
    
    feats = extract_quantum_features(df)
    assert list(feats.columns) == ["transaction_type", "hour_of_day", "day_of_week", "log_amount"]
    assert feats.iloc[0]["transaction_type"] == 5
    assert feats.iloc[0]["hour_of_day"] == 12
    assert feats.iloc[0]["day_of_week"] == 1
    assert abs(feats.iloc[0]["log_amount"] - np.log1p(100.0)) < 1e-5

def test_vqc_circuit_construction():
    fm = ZZFeatureMap(feature_dimension=4, reps=1)
    ansatz = RealAmplitudes(num_qubits=4, entanglement="linear", reps=2)
    qc = fm.compose(ansatz)
    assert qc.num_qubits == 4
    assert len(qc.parameters) == 16 # 4 features in FM + 12 params in Ansatz

def test_vqc_service_predict():
    assert vqc_service.is_available()
    meta = vqc_service.get_metadata()
    assert meta["model_name"] == "vqc"
    assert meta["number_of_qubits"] == 4
    
    sample_tx = {
        "step": 10,
        "type": "CASH_OUT",
        "amount": 500.0
    }
    
    prob, pred_cls = vqc_service.predict(sample_tx)
    assert 0.0 <= prob <= 1.0
    assert pred_cls in (0, 1)
