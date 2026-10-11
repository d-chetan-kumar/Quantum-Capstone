import urllib.request
import json

base_url = 'http://127.0.0.1:8000/api/v1'

def api_call(endpoint, method="GET", data=None):
    url = f"{base_url}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

tests = [
    {
        'category': 'SAFE Case (<0.30)',
        'payload': {
            'amount': 100.0,
            'transaction_type': 'DEBIT',
            'sender_id': 'C_LIVE_SAFE_01',
            'receiver_id': 'M_LIVE_SAFE_01'
        }
    },
    {
        'category': 'REVIEW Case (0.30 to <0.70)',
        'payload': {
            'amount': 200.0,
            'transaction_type': 'PAYMENT',
            'sender_id': 'C_LIVE_REV_02',
            'receiver_id': 'M_LIVE_REV_02'
        }
    },
    {
        'category': 'ALERT Case (>=0.70)',
        'payload': {
            'amount': 50000.0,
            'transaction_type': 'TRANSFER',
            'sender_id': 'C_LIVE_ALERT_03',
            'receiver_id': 'M_LIVE_ALERT_03'
        }
    }
]

print("=== LIVE VERIFICATION: SAFE, REVIEW, ALERT CATEGORIES (50:50 CONFIGURATION) ===\n")

for t in tests:
    data = api_call("/simulator/payment", method="POST", data=t['payload'])
    tx_id = data['transaction_id']
    
    # Query investigation /risk
    r_risk = api_call(f"/transactions/{tx_id}/risk")
    
    # Query behavioural
    r_beh = api_call(f"/transactions/{tx_id}/behaviour")
    
    # Query alerts list
    r_alerts = api_call("/alerts")
    alert_exists = any(a.get('transaction_id') == tx_id for a in r_alerts) if isinstance(r_alerts, list) else False
    
    p_xgb = data['classical_probability']
    p_vqc = data['quantum_probability']
    p_hyb = data['hybrid_probability']
    expected_hyb = round(0.50 * p_xgb + 0.50 * p_vqc, 4)
    
    print(f"Outcome Category: {t['category']}")
    print(f"  Transaction ID:       {tx_id}")
    print(f"  Amount & Type:        INR {data['amount']} {data['transaction_type']}")
    print(f"  Classical XGBoost:    {p_xgb:.4f} ({p_xgb*100:.2f}%)")
    print(f"  Quantum VQC:          {p_vqc:.4f} ({p_vqc*100:.2f}%)")
    print(f"  Hybrid Calculation:   0.50 × {p_xgb:.4f} + 0.50 × {p_vqc:.4f} = {expected_hyb:.4f}")
    print(f"  Engine Hybrid Score:  {p_hyb:.4f} ({p_hyb*100:.2f}%)")
    print(f"  Applied Decision:     {data['risk_level']}")
    print(f"  Investigation Match:  {r_risk['risk_level']} (Hybrid: {r_risk['hybrid_probability']:.4f})")
    print(f"  Fraud Alert Created:  {alert_exists}")
    print(f"  Account Discovery:    Sender={r_beh['sender']['account_id']} ({r_beh['sender']['history_status']}), Receiver={r_beh['receiver']['account_id']}")
    print(f"  Persistence & Time:   Persisted={data['persisted']} in {data['processing_time_ms']} ms\n")
