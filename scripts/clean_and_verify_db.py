import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "quantum_fraud.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

test_senders_query = (
    "SELECT transaction_id FROM transactions WHERE "
    "sender_id = 'abcd' OR "
    "sender_id LIKE 'C_LEAK%' OR "
    "sender_id LIKE 'C_SUFF%' OR "
    "sender_id LIKE 'C_VIC%' OR "
    "sender_id LIKE 'C_NORM%' OR "
    "sender_id LIKE 'C_EP%'"
)
c.execute(test_senders_query)
test_ids = [row[0] for row in c.fetchall()]
print(f"Found {len(test_ids)} test transactions to remove")

if test_ids:
    placeholders = ",".join(["?"] * len(test_ids))
    c.execute(f"DELETE FROM fraud_alerts WHERE transaction_id IN ({placeholders})", test_ids)
    print("Deleted matching test fraud_alerts")
    
    c.execute(f"DELETE FROM model_predictions WHERE transaction_id IN ({placeholders})", test_ids)
    print("Deleted matching test model_predictions")
    
    c.execute(f"DELETE FROM transactions WHERE transaction_id IN ({placeholders})", test_ids)
    print("Deleted test transactions")

conn.commit()

c.execute("SELECT count(*) FROM transactions")
tx_cnt = c.fetchone()[0]

c.execute("SELECT count(*) FROM model_predictions")
pred_cnt = c.fetchone()[0]

c.execute("SELECT count(*) FROM fraud_alerts")
alert_cnt = c.fetchone()[0]

c.execute("SELECT risk_level, count(*) FROM model_predictions GROUP BY risk_level")
risks = dict(c.fetchall())

print(f"\n--- VERIFICATION RESULTS ---")
print(f"Total Transactions: {tx_cnt}")
print(f"Total Predictions:  {pred_cnt}")
print(f"Total Fraud Alerts: {alert_cnt}")
print(f"Risk Decisions:     SAFE={risks.get('SAFE', 0)}, REVIEW={risks.get('REVIEW', 0)}, ALERT={risks.get('ALERT', 0)}")
print(f"Sum of decisions:   {risks.get('SAFE', 0) + risks.get('REVIEW', 0) + risks.get('ALERT', 0)}")
print(f"Match:              {tx_cnt == pred_cnt == (risks.get('SAFE', 0) + risks.get('REVIEW', 0) + risks.get('ALERT', 0))}")

conn.close()
