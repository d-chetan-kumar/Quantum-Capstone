import pytest
from app.services.risk_engine import risk_engine, RiskEngine

def test_hybrid_probability_calculation():
    # Example mathematical verification:
    # XGB = 0.8, VQC = 0.4, weights = 0.3 / 0.7 -> hybrid = 0.3*0.8 + 0.7*0.4 = 0.52
    res = risk_engine.compute_risk(0.8, 0.4)
    assert abs(res["hybrid_probability"] - 0.52) < 1e-4

def test_weight_sum_validation():
    cfg = risk_engine.get_config()
    w_xgb = cfg["xgboost_weight"]
    w_vqc = cfg["vqc_weight"]
    assert abs((w_xgb + w_vqc) - 1.0) < 1e-5

def test_probability_range():
    # Test boundary inputs 0.0 and 1.0
    res_min = risk_engine.compute_risk(0.0, 0.0)
    assert 0.0 <= res_min["hybrid_probability"] <= 1.0
    
    res_max = risk_engine.compute_risk(1.0, 1.0)
    assert 0.0 <= res_max["hybrid_probability"] <= 1.0

def test_risk_threshold_decisions():
    # SAFE decision (< 0.30)
    res_safe = risk_engine.compute_risk(0.1, 0.2)
    assert res_safe["risk_level"] == "SAFE"

    # REVIEW decision (0.30 to < 0.70)
    res_review = risk_engine.compute_risk(0.5, 0.5)
    assert res_review["risk_level"] == "REVIEW"

    # ALERT decision (>= 0.70)
    res_alert = risk_engine.compute_risk(0.9, 0.8)
    assert res_alert["risk_level"] == "ALERT"

def test_feature_dtypes_and_structure():
    import pandas as pd
    import numpy as np
    from app.ml.features import extract_features
    from app.ml.quantum_features import extract_quantum_features

    # Input dictionary with string numbers and object dtypes
    tx_input = {
        'amount': '1500.50',
        'transaction_type': 'TRANSFER',
        'hour_of_day': '14',
        'day_of_week': '2',
        'timestamp': '2026-10-09T13:40:14+05:30'
    }
    df = pd.DataFrame([tx_input])
    
    # 1. Classical Feature Extraction Verification
    feats = extract_features(df)
    expected_cols = ['type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER', 'hour_of_day', 'day_of_week', 'log_amount']
    assert list(feats.columns) == expected_cols
    for col in ['type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER', 'hour_of_day', 'day_of_week']:
        assert pd.api.types.is_integer_dtype(feats[col]), f"Column {col} must be integer"
    assert pd.api.types.is_float_dtype(feats['log_amount']), "log_amount must be float"
    assert feats.dtypes.to_dict() != object, "No columns should remain as object dtype"
    assert np.isfinite(feats.values).all(), "All feature values must be finite"

    # 2. Quantum Feature Extraction Verification
    q_feats = extract_quantum_features(df)
    expected_q_cols = ['transaction_type', 'hour_of_day', 'day_of_week', 'log_amount']
    assert list(q_feats.columns) == expected_q_cols
    for col in expected_q_cols:
        assert pd.api.types.is_float_dtype(q_feats[col]), f"Quantum column {col} must be float64"
    assert np.isfinite(q_feats.values).all(), "All quantum feature values must be finite"

def test_real_model_predictions():
    from app.services.ml_service import ml_service
    from app.ml.vqc_service import vqc_service

    tx = {
        'amount': 2500.0,
        'transaction_type': 'TRANSFER',
        'timestamp': '2026-10-09T13:40:14+05:30'
    }

    # 1. Real XGBoost Prediction Test
    xgb_res = ml_service.predict(tx)
    assert "fraud_probability" in xgb_res
    assert 0.0 <= xgb_res["fraud_probability"] <= 1.0

    # 2. Real VQC Prediction Test
    assert vqc_service.is_available(), f"VQC Service unavailable: {vqc_service.diagnostic_reason}"
    prob, pred_class = vqc_service.predict(tx)
    assert 0.0 <= prob <= 1.0
    assert pred_class in (0, 1)

    # 3. Hybrid Risk Engine Evaluation Test
    eval_res = risk_engine.evaluate_transaction(tx, "test-tx-id")
    assert eval_res["transaction_id"] == "test-tx-id"
    assert 0.0 <= eval_res["classical_probability"] <= 1.0
    assert 0.0 <= eval_res["quantum_probability"] <= 1.0
    assert 0.0 <= eval_res["hybrid_probability"] <= 1.0
    expected_hybrid = 0.3 * eval_res["classical_probability"] + 0.7 * eval_res["quantum_probability"]
    assert abs(eval_res["hybrid_probability"] - expected_hybrid) < 1e-4

