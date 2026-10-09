import pandas as pd
import numpy as np

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Extracts real-time compatible features from PaySim dataset/transactions.
    Ensures all output columns are strictly numeric (int64 or float64) with no object dtypes.
    '''
    df_feat = df.copy()
    
    # Feature 1: log_amount (ensure non-negative and float64)
    amount = pd.to_numeric(df_feat.get('amount', 0.0), errors='coerce').fillna(0.0)
    amount = np.maximum(amount, 0.0)
    df_feat['log_amount'] = np.log1p(amount).astype(np.float64)
    
    # Feature 2: Transaction type encoding (One-hot as int64)
    tx_type = df_feat.get('type', df_feat.get('transaction_type'))
    if isinstance(tx_type, pd.Series):
        tx_type_str = tx_type.astype(str).fillna('UNKNOWN')
    else:
        tx_type_str = pd.Series(['UNKNOWN'] * len(df_feat))
    
    df_feat['type_CASH_IN'] = (tx_type_str == 'CASH_IN').astype(np.int64)
    df_feat['type_CASH_OUT'] = (tx_type_str == 'CASH_OUT').astype(np.int64)
    df_feat['type_DEBIT'] = (tx_type_str == 'DEBIT').astype(np.int64)
    df_feat['type_PAYMENT'] = (tx_type_str == 'PAYMENT').astype(np.int64)
    df_feat['type_TRANSFER'] = (tx_type_str == 'TRANSFER').astype(np.int64)
    
    # Feature 3: Hour of day and Day of week
    if 'hour_of_day' in df_feat.columns and 'day_of_week' in df_feat.columns and df_feat['hour_of_day'].notna().all() and df_feat['day_of_week'].notna().all():
        df_feat['hour_of_day'] = pd.to_numeric(df_feat['hour_of_day'], errors='coerce').fillna(0).astype(np.int64)
        df_feat['day_of_week'] = pd.to_numeric(df_feat['day_of_week'], errors='coerce').fillna(0).astype(np.int64)
    elif 'step' in df_feat.columns and df_feat['step'].notna().all():
        step = pd.to_numeric(df_feat['step'], errors='coerce').fillna(0).astype(np.int64)
        df_feat['hour_of_day'] = (step % 24).astype(np.int64)
        df_feat['day_of_week'] = ((step // 24) % 7).astype(np.int64)
    elif 'timestamp' in df_feat.columns and df_feat['timestamp'].notna().all():
        dt = pd.to_datetime(df_feat['timestamp'], errors='coerce')
        df_feat['hour_of_day'] = dt.dt.hour.fillna(0).astype(np.int64)
        df_feat['day_of_week'] = dt.dt.dayofweek.fillna(0).astype(np.int64)
    else:
        df_feat['hour_of_day'] = np.int64(0)
        df_feat['day_of_week'] = np.int64(0)
        
    expected_cols = [
        'type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER',
        'hour_of_day', 'day_of_week', 'log_amount'
    ]
    
    for col in expected_cols:
        if col not in df_feat.columns:
            df_feat[col] = 0
            
    res = df_feat[expected_cols].copy()
    for col in ['type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER', 'hour_of_day', 'day_of_week']:
        res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0).astype(np.int64)
    res['log_amount'] = pd.to_numeric(res['log_amount'], errors='coerce').fillna(0.0).astype(np.float64)
    
    return res

