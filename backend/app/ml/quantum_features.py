import pandas as pd
import numpy as np

def extract_quantum_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts the exact 4 features required for the Quantum VQC.
    Features: transaction_type, hour_of_day, day_of_week, log_amount
    All output columns are strictly float64 numeric types.
    """
    df_feat = df.copy()
    
    # Feature 1: transaction_type (mapped to int 1-5, float64)
    type_map = {'CASH_IN': 1, 'CASH_OUT': 2, 'DEBIT': 3, 'PAYMENT': 4, 'TRANSFER': 5}
    tx_type = df_feat.get('type', df_feat.get('transaction_type'))
    if isinstance(tx_type, pd.Series):
        df_feat['transaction_type'] = tx_type.astype(str).map(type_map).fillna(0)
    elif isinstance(tx_type, str):
        df_feat['transaction_type'] = type_map.get(tx_type, 0)
    else:
        df_feat['transaction_type'] = 0
    
    # Feature 2 & 3: hour_of_day, day_of_week
    if 'hour_of_day' in df_feat.columns and 'day_of_week' in df_feat.columns and df_feat['hour_of_day'].notna().all() and df_feat['day_of_week'].notna().all():
        df_feat['hour_of_day'] = pd.to_numeric(df_feat['hour_of_day'], errors='coerce').fillna(0)
        df_feat['day_of_week'] = pd.to_numeric(df_feat['day_of_week'], errors='coerce').fillna(0)
    elif 'step' in df_feat.columns and df_feat['step'].notna().all():
        step = pd.to_numeric(df_feat['step'], errors='coerce').fillna(0)
        df_feat['hour_of_day'] = step % 24
        df_feat['day_of_week'] = (step // 24) % 7
    elif 'timestamp' in df_feat.columns and df_feat['timestamp'].notna().all():
        dt = pd.to_datetime(df_feat['timestamp'], errors='coerce')
        df_feat['hour_of_day'] = dt.dt.hour.fillna(0)
        df_feat['day_of_week'] = dt.dt.dayofweek.fillna(0)
    else:
        df_feat['hour_of_day'] = 0
        df_feat['day_of_week'] = 0
        
    # Feature 4: log_amount (ensure non-negative and float64)
    amount = pd.to_numeric(df_feat.get('amount', 0.0), errors='coerce').fillna(0.0)
    amount = np.maximum(amount, 0.0)
    df_feat['log_amount'] = np.log1p(amount)
    
    expected_cols = ['transaction_type', 'hour_of_day', 'day_of_week', 'log_amount']
    
    res = df_feat[expected_cols].copy()
    for col in expected_cols:
        res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0.0).astype(np.float64)
        
    return res

