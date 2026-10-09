import pytest
import pandas as pd
from app.ml.features import extract_features

def test_feature_extraction():
    # Mock data resembling PaySim transaction
    data = [{
        "amount": 1000.50,
        "type": "TRANSFER",
        "nameOrig": "C12345",
        "nameDest": "C67890",
        "isFraud": 1,
        "isFlaggedFraud": 0,
        "step": 12 # hour 12
    }]
    df = pd.DataFrame(data)
    
    features = extract_features(df)
    
    # Check that output has correct columns
    assert "log_amount" in features.columns
    assert "type_TRANSFER" in features.columns
    assert "hour_of_day" in features.columns
    assert "day_of_week" in features.columns
    
    # Check that leakage columns are removed
    assert "isFraud" not in features.columns
    assert "isFlaggedFraud" not in features.columns
    assert "nameOrig" not in features.columns
    assert "nameDest" not in features.columns

def test_type_encoding():
    data = [
        {"amount": 10, "type": "CASH_IN", "step": 1},
        {"amount": 10, "type": "TRANSFER", "step": 1},
        {"amount": 10, "type": "UNKNOWN", "step": 1}
    ]
    df = pd.DataFrame(data)
    features = extract_features(df)
    
    assert features.iloc[0]["type_CASH_IN"] == 1
    assert features.iloc[1]["type_TRANSFER"] == 1
    assert features.iloc[2]["type_CASH_IN"] == 0

def test_time_extraction():
    # step 25 = day 1, hour 1
    data = [{"amount": 10, "type": "TRANSFER", "step": 25}]
    df = pd.DataFrame(data)
    features = extract_features(df)
    
    assert features.iloc[0]["hour_of_day"] == 1
    assert features.iloc[0]["day_of_week"] == 1
