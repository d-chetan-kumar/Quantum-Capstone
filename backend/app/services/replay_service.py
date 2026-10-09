import asyncio
import os
import sys
import logging
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.services.payment_service import payment_service
from app.services.realtime_service import realtime_manager

logger = logging.getLogger("replay_service")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DATA_PATHS = [
    os.path.join(PROJECT_ROOT, "data", "PS_20174392719_1491204439457_log.csv"),
    os.path.abspath("data/PS_20174392719_1491204439457_log.csv")
]

COLS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg",
    "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest",
    "isFraud", "isFlaggedFraud"
]

class ReplayService:
    def __init__(self):
        self.is_replaying: bool = False
        self.current_step: int = 0
        self.total_records: int = 200
        self.speed: int = 1
        self._task: Optional[asyncio.Task] = None
        self._df_sample: Optional[pd.DataFrame] = None

    def _load_sample_data(self):
        if self._df_sample is not None:
            return self._df_sample

        csv_path = None
        for p in DATA_PATHS:
            if os.path.exists(p):
                csv_path = p
                break

        if not csv_path:
            raise FileNotFoundError("PaySim CSV file not found.")

        header_idx = None
        with open(csv_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if "step,type,amount" in line and "log_amount" not in line:
                    header_idx = idx
                    break

        if header_idx is None:
            df = pd.read_csv(csv_path)
        else:
            df = pd.read_csv(csv_path, skiprows=header_idx + 1, header=None, names=COLS)

        df = df.sort_values(by='step')

        total_rows = len(df)
        val_idx = int(total_rows * 0.85)
        test_df = df.iloc[val_idx:]

        test_fraud = test_df[test_df['isFraud'] == 1].sample(n=min(100, (test_df['isFraud'] == 1).sum()), random_state=42)
        test_non_fraud = test_df[test_df['isFraud'] == 0].sample(n=min(100, (test_df['isFraud'] == 0).sum()), random_state=42)

        self._df_sample = pd.concat([test_fraud, test_non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)
        self.total_records = len(self._df_sample)
        return self._df_sample

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_replaying": self.is_replaying,
            "processed": self.current_step,
            "total": self.total_records,
            "speed": self.speed
        }

    async def start_replay(self, speed: int = 1):
        if self.is_replaying:
            return {"status": "error", "message": "Replay session already in progress."}

        self.speed = max(1, min(speed, 5))
        self.is_replaying = True
        self.current_step = 0
        self._task = asyncio.create_task(self._run_replay_loop())

        return {
            "status": "started",
            "speed": self.speed,
            "total_records": self.total_records
        }

    async def stop_replay(self):
        if not self.is_replaying:
            return {"status": "ok", "message": "Replay is not running."}

        self.is_replaying = False
        if self._task and not self._task.done():
            self._task.cancel()

        return {"status": "stopped", "processed": self.current_step}

    async def _run_replay_loop(self):
        try:
            sample_df = self._load_sample_data()
            interval = 2.0 / float(self.speed)

            for idx, row in sample_df.iterrows():
                if not self.is_replaying:
                    break

                db = SessionLocal()
                try:
                    res = await payment_service.process_payment(
                        amount=float(row['amount']),
                        transaction_type=str(row['type']),
                        sender_id=str(row['nameOrig']),
                        receiver_id=str(row['nameDest']),
                        db=db
                    )
                    self.current_step += 1
                except Exception as e:
                    logger.error(f"Error processing replay item {idx}: {e}")
                finally:
                    db.close()

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("Replay task cancelled.")
        except Exception as e:
            logger.error(f"Error in replay loop: {e}")
        finally:
            self.is_replaying = False

replay_service = ReplayService()
