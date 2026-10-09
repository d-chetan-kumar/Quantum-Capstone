import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, and_

from app.models.transaction import Transaction
from app.models.alert import FraudAlert

logger = logging.getLogger(__name__)

MIN_HISTORY_THRESHOLD = 3

class BehaviouralRiskService:
    def get_account_profile(
        self,
        account_id: str,
        current_tx_id: Optional[str] = None,
        as_of_time: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Discovers account profile automatically from transaction history.
        Tracks roles (SENDER, RECEIVER), transaction counts, total amounts, and first/last seen.
        """
        if not db or not account_id:
            return {
                "account_id": account_id,
                "is_known": False,
                "roles": [],
                "history_status": "NO_HISTORY",
                "total_transactions_count": 0,
                "as_sender_count": 0,
                "as_receiver_count": 0,
                "first_seen": None,
                "last_seen": None
            }

        # Build query for transactions involving this account
        sender_q = db.query(Transaction).filter(Transaction.sender_id == account_id)
        receiver_q = db.query(Transaction).filter(Transaction.receiver_id == account_id)

        # Prevent data leakage: exclude current transaction if specified
        if current_tx_id:
            sender_q = sender_q.filter(Transaction.transaction_id != current_tx_id)
            receiver_q = receiver_q.filter(Transaction.transaction_id != current_tx_id)

        # Exclude future transactions relative to point-in-time calculation
        if as_of_time:
            sender_q = sender_q.filter(
                or_(Transaction.created_at < as_of_time, Transaction.timestamp < as_of_time)
            )
            receiver_q = receiver_q.filter(
                or_(Transaction.created_at < as_of_time, Transaction.timestamp < as_of_time)
            )

        sent_txs = sender_q.all()
        received_txs = receiver_q.all()

        as_sender_count = len(sent_txs)
        as_receiver_count = len(received_txs)
        total_count = as_sender_count + as_receiver_count

        if total_count == 0:
            return {
                "account_id": account_id,
                "is_known": False,
                "roles": [],
                "history_status": "NEWLY_OBSERVED",
                "total_transactions_count": 0,
                "as_sender_count": 0,
                "as_receiver_count": 0,
                "first_seen": None,
                "last_seen": None
            }

        roles = []
        if as_sender_count > 0:
            roles.append("SENDER")
        if as_receiver_count > 0:
            roles.append("RECEIVER")

        all_txs = sent_txs + received_txs
        all_times = [
            t.created_at or t.timestamp for t in all_txs if (t.created_at or t.timestamp)
        ]
        
        first_seen = min(all_times).isoformat() if all_times else None
        last_seen = max(all_times).isoformat() if all_times else None

        history_status = "SUFFICIENT_HISTORY" if total_count >= MIN_HISTORY_THRESHOLD else "INSUFFICIENT_HISTORY"

        return {
            "account_id": account_id,
            "is_known": True,
            "roles": roles,
            "history_status": history_status,
            "total_transactions_count": total_count,
            "as_sender_count": as_sender_count,
            "as_receiver_count": as_receiver_count,
            "first_seen": first_seen,
            "last_seen": last_seen
        }

    def compute_sender_behaviour(
        self,
        sender_id: str,
        current_amount: float,
        current_tx_id: Optional[str] = None,
        as_of_time: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Calculates historical sender behavioural metrics excluding the current transaction.
        """
        if not db or not sender_id:
            return {
                "sender_id": sender_id,
                "history_status": "NO_HISTORY",
                "previous_tx_count": 0,
                "total_sent_amount": 0.0,
                "avg_sent_amount": 0.0,
                "max_sent_amount": 0.0,
                "distinct_recipients_count": 0,
                "recent_24h_tx_count": 0,
                "time_since_last_tx_seconds": None,
                "amount_deviation_ratio": 1.0
            }

        q = db.query(Transaction).filter(Transaction.sender_id == sender_id)

        # Prevent data leakage: exclude current transaction
        if current_tx_id:
            q = q.filter(Transaction.transaction_id != current_tx_id)

        # Filter strictly prior transactions if point-in-time specified
        if as_of_time:
            q = q.filter(
                or_(Transaction.created_at < as_of_time, Transaction.timestamp < as_of_time)
            )

        past_txs = q.order_by(desc(Transaction.created_at)).all()
        tx_count = len(past_txs)

        if tx_count == 0:
            return {
                "sender_id": sender_id,
                "history_status": "NEWLY_OBSERVED",
                "previous_tx_count": 0,
                "total_sent_amount": 0.0,
                "avg_sent_amount": 0.0,
                "max_sent_amount": 0.0,
                "distinct_recipients_count": 0,
                "recent_24h_tx_count": 0,
                "time_since_last_tx_seconds": None,
                "amount_deviation_ratio": 1.0
            }

        amounts = [t.amount for t in past_txs if t.amount is not None]
        total_sent = sum(amounts)
        avg_sent = total_sent / len(amounts) if amounts else 0.0
        max_sent = max(amounts) if amounts else 0.0

        distinct_recipients = len({t.receiver_id for t in past_txs if t.receiver_id})

        # Calculate time since last transaction
        last_tx_time = past_txs[0].created_at or past_txs[0].timestamp
        time_since_last_sec = None
        recent_24h_count = 0

        ref_time = as_of_time or datetime.now(timezone.utc)
        if last_tx_time:
            if last_tx_time.tzinfo is None:
                last_tx_time = last_tx_time.replace(tzinfo=timezone.utc)
            if ref_time.tzinfo is None:
                ref_time = ref_time.replace(tzinfo=timezone.utc)
            
            time_since_last_sec = max(0.0, (ref_time - last_tx_time).total_seconds())

            twenty_four_hours_ago = ref_time - timedelta(hours=24)
            recent_24h_count = sum(
                1 for t in past_txs
                if (t.created_at or t.timestamp) and (
                    (t.created_at or t.timestamp).replace(tzinfo=timezone.utc) if (t.created_at or t.timestamp).tzinfo is None else (t.created_at or t.timestamp)
                ) >= twenty_four_hours_ago
            )

        # Deviation ratio
        amount_ratio = round(current_amount / avg_sent, 2) if avg_sent > 0 else 1.0

        history_status = "SUFFICIENT_HISTORY" if tx_count >= MIN_HISTORY_THRESHOLD else "INSUFFICIENT_HISTORY"

        return {
            "sender_id": sender_id,
            "history_status": history_status,
            "previous_tx_count": tx_count,
            "total_sent_amount": round(total_sent, 2),
            "avg_sent_amount": round(avg_sent, 2),
            "max_sent_amount": round(max_sent, 2),
            "distinct_recipients_count": distinct_recipients,
            "recent_24h_tx_count": recent_24h_count,
            "time_since_last_tx_seconds": round(time_since_last_sec, 1) if time_since_last_sec is not None else None,
            "amount_deviation_ratio": amount_ratio
        }

    def compute_receiver_behaviour(
        self,
        receiver_id: str,
        current_tx_id: Optional[str] = None,
        as_of_time: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Calculates historical receiver risk metrics and prior verified fraud alerts.
        """
        if not db or not receiver_id:
            return {
                "receiver_id": receiver_id,
                "history_status": "NO_HISTORY",
                "previous_received_count": 0,
                "total_received_amount": 0.0,
                "avg_received_amount": 0.0,
                "verified_alerts_count": 0,
                "unresolved_alerts_count": 0
            }

        q = db.query(Transaction).filter(Transaction.receiver_id == receiver_id)

        if current_tx_id:
            q = q.filter(Transaction.transaction_id != current_tx_id)

        if as_of_time:
            q = q.filter(
                or_(Transaction.created_at < as_of_time, Transaction.timestamp < as_of_time)
            )

        past_txs = q.all()
        rcv_count = len(past_txs)

        amounts = [t.amount for t in past_txs if t.amount is not None]
        total_rcv = sum(amounts)
        avg_rcv = total_rcv / len(amounts) if amounts else 0.0

        # Query verified fraud alerts associated with past transactions of this receiver
        past_tx_ids = [t.transaction_id for t in past_txs]
        verified_alerts = 0
        unresolved_alerts = 0

        if past_tx_ids:
            alerts = db.query(FraudAlert).filter(FraudAlert.transaction_id.in_(past_tx_ids)).all()
            verified_alerts = len(alerts)
            unresolved_alerts = sum(1 for a in alerts if not a.resolved)

        history_status = "SUFFICIENT_HISTORY" if rcv_count >= MIN_HISTORY_THRESHOLD else "INSUFFICIENT_HISTORY"
        if rcv_count == 0:
            history_status = "NEWLY_OBSERVED"

        return {
            "receiver_id": receiver_id,
            "history_status": history_status,
            "previous_received_count": rcv_count,
            "total_received_amount": round(total_rcv, 2),
            "avg_received_amount": round(avg_rcv, 2),
            "verified_alerts_count": verified_alerts,
            "unresolved_alerts_count": unresolved_alerts
        }

    def evaluate_transaction_behaviour(
        self,
        transaction_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Main behavioural evaluation method for a transaction.
        Calculates historical features without data leakage, extracts indicators, and returns explainable summary.
        """
        tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not tx:
            return {
                "error": f"Transaction '{transaction_id}' not found",
                "behavioural_risk_signal": "UNKNOWN"
            }

        ref_time = tx.created_at or tx.timestamp or datetime.now(timezone.utc)

        sender_profile = self.get_account_profile(
            account_id=tx.sender_id,
            current_tx_id=tx.transaction_id,
            as_of_time=ref_time,
            db=db
        )

        receiver_profile = self.get_account_profile(
            account_id=tx.receiver_id,
            current_tx_id=tx.transaction_id,
            as_of_time=ref_time,
            db=db
        )

        sender_behaviour = self.compute_sender_behaviour(
            sender_id=tx.sender_id,
            current_amount=tx.amount,
            current_tx_id=tx.transaction_id,
            as_of_time=ref_time,
            db=db
        )

        receiver_behaviour = self.compute_receiver_behaviour(
            receiver_id=tx.receiver_id,
            current_tx_id=tx.transaction_id,
            as_of_time=ref_time,
            db=db
        )

        indicators = []
        risk_score = 0.0

        # Indicator 1: Newly observed sender
        if not sender_profile["is_known"]:
            indicators.append({
                "type": "HISTORICAL_OBSERVATION",
                "code": "NEW_SENDER_ACCOUNT",
                "severity": "LOW",
                "title": "Newly Observed Sender Account",
                "explanation": f"Sender account '{tx.sender_id}' has not appeared in prior transaction records."
            })

        # Indicator 2: Newly observed receiver
        if not receiver_profile["is_known"]:
            indicators.append({
                "type": "HISTORICAL_OBSERVATION",
                "code": "NEW_RECEIVER_ACCOUNT",
                "severity": "LOW",
                "title": "Newly Observed Receiver Account",
                "explanation": f"Receiver account '{tx.receiver_id}' has not received prior payments in recorded history."
            })

        # Indicator 3: Insufficient sender history
        if sender_behaviour["history_status"] == "INSUFFICIENT_HISTORY":
            indicators.append({
                "type": "HISTORICAL_OBSERVATION",
                "code": "INSUFFICIENT_SENDER_HISTORY",
                "severity": "INFO",
                "title": "Insufficient Sender History",
                "explanation": f"Sender has only {sender_behaviour['previous_tx_count']} prior transaction(s). At least {MIN_HISTORY_THRESHOLD} are required for robust statistical baseline."
            })

        # Indicator 4: Amount Deviation (Heuristic - ONLY evaluated when baseline is available)
        if sender_behaviour["history_status"] == "SUFFICIENT_HISTORY":
            ratio = sender_behaviour["amount_deviation_ratio"]
            if ratio >= 5.0:
                risk_score += 0.4
                indicators.append({
                    "type": "HEURISTIC_INDICATOR",
                    "code": "HIGH_AMOUNT_DEVIATION",
                    "severity": "HIGH",
                    "title": "Extreme Amount Spurt",
                    "explanation": f"Payment amount of ₹{tx.amount:,.2f} is {ratio:.1f}x higher than sender's historical average of ₹{sender_behaviour['avg_sent_amount']:,.2f}."
                })
            elif ratio >= 2.5:
                risk_score += 0.2
                indicators.append({
                    "type": "HEURISTIC_INDICATOR",
                    "code": "MODERATE_AMOUNT_DEVIATION",
                    "severity": "MODERATE",
                    "title": "Elevated Amount Deviation",
                    "explanation": f"Payment amount of ₹{tx.amount:,.2f} is {ratio:.1f}x higher than sender's historical average of ₹{sender_behaviour['avg_sent_amount']:,.2f}."
                })

        # Indicator 5: Rapid transaction burst in 24h (Heuristic)
        if sender_behaviour["recent_24h_tx_count"] >= 5:
            risk_score += 0.3
            indicators.append({
                "type": "HEURISTIC_INDICATOR",
                "code": "HIGH_TRANSACTION_BURST",
                "severity": "HIGH",
                "title": "Rapid Transaction Frequency",
                "explanation": f"Sender initiated {sender_behaviour['recent_24h_tx_count']} transactions in the last 24 hours."
            })

        # Indicator 6: Receiver with prior unresolved fraud alerts (VERIFIED EVIDENCE)
        if receiver_behaviour["unresolved_alerts_count"] > 0:
            risk_score += 0.5
            indicators.append({
                "type": "VERIFIED_EVIDENCE",
                "code": "RECEIVER_WITH_ACTIVE_ALERTS",
                "severity": "HIGH",
                "title": "Receiver Account Associated with Fraud Alerts",
                "explanation": f"Receiver account '{tx.receiver_id}' has {receiver_behaviour['unresolved_alerts_count']} active, unresolved fraud alert(s) on record."
            })
        elif receiver_behaviour["verified_alerts_count"] > 0:
            risk_score += 0.2
            indicators.append({
                "type": "VERIFIED_EVIDENCE",
                "code": "RECEIVER_HISTORICAL_ALERTS",
                "severity": "MODERATE",
                "title": "Receiver Historical Alert History",
                "explanation": f"Receiver account '{tx.receiver_id}' has {receiver_behaviour['verified_alerts_count']} historical fraud alert record(s)."
            })

        # Determine overall behavioural risk signal
        if sender_behaviour["history_status"] in ["NO_HISTORY", "NEWLY_OBSERVED"] and receiver_behaviour["history_status"] in ["NO_HISTORY", "NEWLY_OBSERVED"]:
            behavioural_signal = "INSUFFICIENT_DATA"
            summary = "Automatic account discovery logged new sender and receiver accounts. Insufficient history to establish behavioural baseline."
        elif risk_score >= 0.5:
            behavioural_signal = "SUSPICIOUS"
            summary = f"Behavioural risk analysis flagged elevated risk indicators (score: {risk_score:.2f}). Require further analyst investigation."
        elif risk_score > 0.0:
            behavioural_signal = "ELEVATED"
            summary = f"Minor behavioural heuristics detected (score: {risk_score:.2f}). Sender baseline available."
        else:
            behavioural_signal = "NORMAL"
            summary = "Transaction aligns with historical sender pattern and receiver profile."

        return {
            "transaction_id": str(tx.transaction_id),
            "amount": float(tx.amount),
            "sender": {**sender_profile, **sender_behaviour},
            "receiver": {**receiver_profile, **receiver_behaviour},
            "indicators": indicators,
            "behavioural_risk_score": round(risk_score, 2),
            "behavioural_risk_signal": behavioural_signal,
            "summary": summary
        }

behavioural_risk_service = BehaviouralRiskService()
