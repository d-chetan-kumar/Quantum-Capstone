import os
import json

BASE_DIR = r"c:\Users\HP\OneDrive\Desktop\QUANTUM FRAUD DETECTION"

def write_file(path, content):
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 1. Update requirements.txt
write_file("backend/requirements.txt", """
fastapi==0.103.2
uvicorn==0.23.2
sqlalchemy==2.0.21
psycopg2-binary==2.9.9
alembic==1.12.0
pydantic==2.4.2
pydantic-settings==2.0.3
websockets==11.0.3
pytest==7.4.2
xgboost==2.0.3
pandas==2.1.1
scikit-learn==1.3.1
numpy==1.26.0
""")

# 2. Database Model Update (prediction.py)
write_file("backend/app/models/prediction.py", """
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base

class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.transaction_id"))
    
    # ML Details
    model_name = Column(String)
    model_version = Column(String)
    
    # Classical AI
    fraud_probability = Column(Float)
    predicted_class = Column(Integer)
    
    # Kept for future phases
    quantum_probability = Column(Float, nullable=True)
    hybrid_probability = Column(Float, nullable=True)
    final_risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    
    execution_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
""")

# 3. ML Pipeline and Service
write_file("backend/app/ml/features.py", """
import pandas as pd
import numpy as np

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Extracts real-time compatible features from PaySim dataset/transactions.
    Assumes standard PaySim columns: type, amount, nameOrig, nameDest, etc.
    '''
    # We create a copy to avoid SettingWithCopyWarning
    df_feat = df.copy()
    
    # Feature 1: log_amount
    df_feat['log_amount'] = np.log1p(df_feat['amount'])
    
    # Feature 2: Transaction type encoding (One-hot or numeric)
    # PaySim types: CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER
    type_map = {'CASH_IN': 1, 'CASH_OUT': 2, 'DEBIT': 3, 'PAYMENT': 4, 'TRANSFER': 5}
    # For robust API usage, map unknown types to 0
    df_feat['type_encoded'] = df_feat.get('type', df_feat.get('transaction_type')).map(type_map).fillna(0).astype(int)
    
    # Feature 3: Hour of day (simulated from step if dataset, or timestamp if real API)
    if 'step' in df_feat.columns:
        # PaySim step is 1 hour of time
        df_feat['hour_of_day'] = df_feat['step'] % 24
        df_feat['day_of_week'] = (df_feat['step'] // 24) % 7
    elif 'timestamp' in df_feat.columns:
        # From API transaction
        dt = pd.to_datetime(df_feat['timestamp'])
        df_feat['hour_of_day'] = dt.dt.hour
        df_feat['day_of_week'] = dt.dt.dayofweek
    else:
        df_feat['hour_of_day'] = 0
        df_feat['day_of_week'] = 0
        
    # Exclude leakage-prone columns: isFraud, isFlaggedFraud, nameOrig, nameDest
    # Ensure consistent column ordering for XGBoost
    expected_cols = ['log_amount', 'type_encoded', 'hour_of_day', 'day_of_week']
    
    return df_feat[expected_cols]
""")

write_file("backend/app/ml/train_xgboost.py", """
import os
import json
import time
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
from app.ml.features import extract_features

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/PS_20174392719_1491204439457_log.csv")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "../../../artifacts/models")

def train():
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}. Please download PaySim dataset.")
        return

    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # Chronological Split (Train: first 70%, Val: next 15%, Test: last 15%)
    print("Splitting dataset chronologically...")
    df = df.sort_values(by='step')
    
    train_idx = int(len(df) * 0.7)
    val_idx = int(len(df) * 0.85)
    
    train_df = df.iloc[:train_idx]
    val_df = df.iloc[train_idx:val_idx]
    test_df = df.iloc[val_idx:]
    
    print("Feature Engineering...")
    X_train = extract_features(train_df)
    y_train = train_df['isFraud']
    
    X_val = extract_features(val_df)
    y_val = val_df['isFraud']
    
    X_test = extract_features(test_df)
    y_test = test_df['isFraud']
    
    print("Training XGBoost...")
    params = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'scale_pos_weight': len(y_train[y_train == 0]) / len(y_train[y_train == 1]) if len(y_train[y_train == 1]) > 0 else 1
    }
    
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=10)
    
    print("Evaluating on Test Set...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    metrics = {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "confusion_matrix": cm
    }
    
    print("Metrics:", json.dumps(metrics, indent=2))
    
    print("Saving artifacts...")
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    model_path = os.path.join(ARTIFACTS_DIR, "xgboost_fraud_model.json")
    model.save_model(model_path)
    
    metadata = {
        "model_name": "xgboost_paysim",
        "model_version": "v1.0",
        "training_timestamp": time.time(),
        "feature_names": X_train.columns.tolist(),
        "hyperparameters": params,
        "evaluation_metrics": metrics
    }
    
    with open(os.path.join(ARTIFACTS_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print("Training complete.")

if __name__ == "__main__":
    train()
""")

write_file("backend/app/services/ml_service.py", """
import os
import json
import time
import pandas as pd
import xgboost as xgb
from app.ml.features import extract_features

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "../../../artifacts/models")

class MLService:
    def __init__(self):
        self.model = None
        self.metadata = None
        self._load_model()
        
    def _load_model(self):
        model_path = os.path.join(ARTIFACTS_DIR, "xgboost_fraud_model.json")
        meta_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
        
        if os.path.exists(model_path) and os.path.exists(meta_path):
            self.model = xgb.XGBClassifier()
            self.model.load_model(model_path)
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)
                
    def get_status(self):
        if not self.model or not self.metadata:
            return {"status": "unavailable", "message": "Model artifacts not found"}
            
        return {
            "status": "available",
            "model_name": self.metadata.get("model_name"),
            "model_version": self.metadata.get("model_version"),
            "training_timestamp": self.metadata.get("training_timestamp"),
            "feature_count": len(self.metadata.get("feature_names", [])),
            "metrics": self.metadata.get("evaluation_metrics", {})
        }
        
    def predict(self, transaction_dict: dict) -> dict:
        if not self.model:
            raise Exception("Model not loaded")
            
        start_time = time.time()
        df = pd.DataFrame([transaction_dict])
        features = extract_features(df)
        
        # XGBoost expects the exact feature order
        if self.metadata and "feature_names" in self.metadata:
            features = features[self.metadata["feature_names"]]
            
        prob = float(self.model.predict_proba(features)[0][1])
        pred_class = int(self.model.predict(features)[0])
        exec_time = (time.time() - start_time) * 1000
        
        return {
            "fraud_probability": prob,
            "predicted_class": pred_class,
            "execution_time_ms": exec_time,
            "model_name": self.metadata.get("model_name", "unknown"),
            "model_version": self.metadata.get("model_version", "unknown")
        }

ml_service = MLService()
""")

# 4. Update API
write_file("backend/app/api/v1/models.py", """
from fastapi import APIRouter
from app.services.ml_service import ml_service

router = APIRouter()

@router.get("/xgboost/status")
def get_model_status():
    return ml_service.get_status()
""")

write_file("backend/app/api/v1/__init__.py", """
from fastapi import APIRouter
from app.api.v1.transactions import router as transactions_router
from app.api.v1.models import router as models_router

router = APIRouter()
router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
router.include_router(models_router, prefix="/models", tags=["models"])
""")

write_file("backend/app/schemas/prediction.py", """
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class PredictionResponse(BaseModel):
    prediction_id: UUID
    transaction_id: UUID
    model_name: str
    model_version: str
    fraud_probability: float
    predicted_class: int
    execution_time_ms: float
    created_at: datetime
    
    class Config:
        from_attributes = True
""")

# Overwrite transactions API to add predict endpoint
write_file("backend/app/api/v1/transactions.py", """
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, Any
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionListResponse
from app.schemas.prediction import PredictionResponse
from app.models.transaction import Transaction
from app.models.prediction import ModelPrediction
from app.db.session import SessionLocal
from app.services.ml_service import ml_service

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TransactionResponse)
def create_transaction(transaction_in: TransactionCreate, db: Session = Depends(get_db)):
    db_obj = Transaction(**transaction_in.model_dump(), status="PENDING")
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=TransactionListResponse)
def read_transactions(skip: int = 0, limit: int = 50, transaction_type: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Transaction)
    if transaction_type: query = query.filter(Transaction.transaction_type == transaction_type)
    if status: query = query.filter(Transaction.status == status)
    
    total = query.count()
    items = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit).all()
    return TransactionListResponse(items=items, total=total, page=(skip // limit) + 1, size=limit)

@router.get("/{transaction_id}", response_model=TransactionResponse)
def read_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx: raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

@router.post("/{transaction_id}/predict", response_model=PredictionResponse)
def predict_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx: raise HTTPException(status_code=404, detail="Transaction not found")
    
    try:
        tx_dict = {
            "amount": tx.amount,
            "transaction_type": tx.transaction_type,
            "timestamp": tx.timestamp.isoformat()
        }
        pred_result = ml_service.predict(tx_dict)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    pred_obj = ModelPrediction(
        transaction_id=tx.transaction_id,
        model_name=pred_result["model_name"],
        model_version=pred_result["model_version"],
        fraud_probability=pred_result["fraud_probability"],
        predicted_class=pred_result["predicted_class"],
        execution_time_ms=pred_result["execution_time_ms"]
    )
    db.add(pred_obj)
    db.commit()
    db.refresh(pred_obj)
    return pred_obj

@router.get("/{transaction_id}/predict", response_model=PredictionResponse)
def get_prediction(transaction_id: str, db: Session = Depends(get_db)):
    pred = db.query(ModelPrediction).filter(ModelPrediction.transaction_id == transaction_id).order_by(desc(ModelPrediction.created_at)).first()
    if not pred: raise HTTPException(status_code=404, detail="Prediction not found")
    return pred
""")

# 5. Frontend Pages
write_file("frontend/src/pages/AIModels.tsx", """
import { useEffect, useState } from 'react';
import axios from 'axios';
import { Cpu, Activity, AlertCircle } from 'lucide-react';

export default function AIModels() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await axios.get(import.meta.env.VITE_API_BASE_URL + '/models/xgboost/status');
        setStatus(res.data);
      } catch (err) {
        setStatus({ status: 'error' });
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading model status...</div>;

  const isAvailable = status?.status === 'available';

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">AI Models Portfolio</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* XGBoost Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-4">
             <Cpu size={24} className="text-indigo-600 dark:text-indigo-400" />
             <h2 className="text-xl font-bold">Classical AI (XGBoost)</h2>
          </div>
          
          {isAvailable ? (
            <div className="space-y-4 text-sm">
               <div className="grid grid-cols-2 gap-2">
                 <span className="text-slate-500">Status</span>
                 <span className="text-green-600 font-medium text-right">Available</span>
                 <span className="text-slate-500">Version</span>
                 <span className="text-right">{status.model_version}</span>
                 <span className="text-slate-500">Feature Count</span>
                 <span className="text-right">{status.feature_count}</span>
                 <span className="text-slate-500">Trained At</span>
                 <span className="text-right">{new Date(status.training_timestamp * 1000).toLocaleString()}</span>
               </div>
               
               <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
                 <h3 className="font-semibold mb-2">Evaluation Metrics</h3>
                 {status.metrics ? (
                   <div className="grid grid-cols-2 gap-2">
                     <span className="text-slate-500">Precision</span>
                     <span className="text-right">{(status.metrics.precision * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">Recall</span>
                     <span className="text-right">{(status.metrics.recall * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">F1 Score</span>
                     <span className="text-right">{(status.metrics.f1_score * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">ROC-AUC</span>
                     <span className="text-right">{(status.metrics.roc_auc * 100).toFixed(2)}%</span>
                   </div>
                 ) : (
                   <span className="text-slate-400 italic">Evaluation not available</span>
                 )}
               </div>
            </div>
          ) : (
             <div className="p-4 bg-slate-50 dark:bg-slate-800/50 text-slate-500 text-center rounded-lg border border-dashed border-slate-300 dark:border-slate-700">
                <AlertCircle className="mx-auto mb-2 text-slate-400" />
                Model artifacts not found.<br/>Please run training pipeline.
             </div>
          )}
        </div>

        {/* VQC Card (Placeholder) */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 opacity-60">
          <div className="flex items-center gap-3 mb-4">
             <Activity size={24} className="text-fuchsia-600 dark:text-fuchsia-400" />
             <h2 className="text-xl font-bold">Quantum AI (VQC)</h2>
          </div>
          <p className="text-slate-500 text-sm">Implementation pending (Future Phase)</p>
        </div>

      </div>
    </div>
  );
}
""")

write_file("frontend/src/pages/TransactionDetail.tsx", """
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, ShieldAlert, Cpu } from 'lucide-react';

export default function TransactionDetail() {
  const { id } = useParams();
  const [tx, setTx] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTx = async () => {
      try {
        const res = await axios.get(import.meta.env.VITE_API_BASE_URL + `/transactions/${id}`);
        setTx(res.data);
        
        try {
            const predRes = await axios.get(import.meta.env.VITE_API_BASE_URL + `/transactions/${id}/predict`);
            setPrediction(predRes.data);
        } catch (e) {
            // No prediction yet
        }
      } catch (err: any) {
        setError('Transaction not found or backend unavailable');
      } finally {
        setLoading(false);
      }
    };
    fetchTx();
  }, [id]);

  const handlePredict = async () => {
    setAnalyzing(true);
    try {
        const res = await axios.post(import.meta.env.VITE_API_BASE_URL + `/transactions/${id}/predict`);
        setPrediction(res.data);
    } catch (err: any) {
        alert(err.response?.data?.detail || "Failed to analyze");
    } finally {
        setAnalyzing(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/transactions" className="p-2 bg-slate-200 dark:bg-slate-800 rounded-full hover:bg-slate-300 dark:hover:bg-slate-700 transition">
          <ArrowLeft size={20} />
        </Link>
        <h1 className="text-3xl font-bold">Transaction Investigation</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <div className="md:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <h2 className="text-xl font-semibold mb-4">Payment Details</h2>
          <div className="grid grid-cols-2 gap-y-4 text-sm">
            <div><span className="text-slate-500 block">Transaction ID</span><span className="font-mono">{tx.transaction_id}</span></div>
            <div><span className="text-slate-500 block">Status</span><span className="font-medium text-yellow-600">{tx.status}</span></div>
            <div><span className="text-slate-500 block">Amount</span><span className="font-medium text-lg">₹{tx.amount.toLocaleString()}</span></div>
            <div><span className="text-slate-500 block">Type</span><span>{tx.transaction_type}</span></div>
            <div><span className="text-slate-500 block">Sender</span><span className="font-mono">{tx.sender_id}</span></div>
            <div><span className="text-slate-500 block">Receiver</span><span className="font-mono">{tx.receiver_id}</span></div>
            <div><span className="text-slate-500 block">Timestamp</span><span>{new Date(tx.timestamp).toLocaleString()}</span></div>
            <div><span className="text-slate-500 block">Simulated</span><span>{tx.is_simulated ? 'Yes' : 'No'}</span></div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
             <div className="flex items-center justify-between mb-4">
                 <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                     <Cpu size={20} className="text-indigo-500" /> 
                     <h2 className="text-lg font-semibold">Classical AI</h2>
                 </div>
             </div>
             
             {analyzing ? (
                 <p className="text-indigo-500 text-sm animate-pulse">Analyzing transaction...</p>
             ) : prediction ? (
                 <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <span className="text-slate-500">Fraud Probability</span>
                        <span className={`font-bold text-lg ${prediction.fraud_probability > 0.5 ? 'text-red-500' : 'text-green-500'}`}>
                            {(prediction.fraud_probability * 100).toFixed(1)}%
                        </span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <span className="text-slate-500">Predicted Class</span>
                        <span className="font-medium">{prediction.predicted_class === 1 ? 'FRAUD' : 'LEGITIMATE'}</span>
                    </div>
                    <div className="text-xs text-slate-400 mt-2">
                        Model: {prediction.model_name} {prediction.model_version} <br/>
                        Analyzed at: {new Date(prediction.created_at).toLocaleString()}
                    </div>
                 </div>
             ) : (
                 <div className="text-center">
                    <p className="text-slate-500 text-sm italic mb-4">Not evaluated yet</p>
                    <button onClick={handlePredict} className="w-full py-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition">
                        Run XGBoost Analysis
                    </button>
                 </div>
             )}
          </div>

          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 opacity-60">
             <div className="flex items-center gap-2 mb-4 text-slate-700 dark:text-slate-300">
                 <ShieldAlert size={20} className="text-fuchsia-500" /> 
                 <h2 className="text-lg font-semibold">Quantum AI (VQC)</h2>
             </div>
             <p className="text-slate-500 text-sm italic">Pending Phase Integration</p>
          </div>
        </div>

      </div>
    </div>
  );
}
""")

write_file("frontend/src/App.tsx", """
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import Dashboard from './pages/Dashboard';
import LivePayments from './pages/LivePayments';
import Settings from './pages/Settings';
import EmptyStatePage from './pages/EmptyStatePage';
import Transactions from './pages/Transactions';
import NewPayment from './pages/NewPayment';
import TransactionDetail from './pages/TransactionDetail';
import AIModels from './pages/AIModels';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<RootLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="live" element={<LivePayments />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="transactions/new" element={<NewPayment />} />
          <Route path="transactions/:id" element={<TransactionDetail />} />
          <Route path="alerts" element={<EmptyStatePage title="Alerts" />} />
          <Route path="analytics" element={<EmptyStatePage title="Analytics" />} />
          <Route path="models" element={<AIModels />} />
          <Route path="vqc-lab" element={<EmptyStatePage title="VQC Lab" />} />
          <Route path="methodology" element={<EmptyStatePage title="Methodology" />} />
          <Route path="simulator" element={<EmptyStatePage title="Simulator" />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
""")

write_file("frontend/src/layouts/RootLayout.tsx", """
import { Outlet, Link } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { Activity, LayoutDashboard, Settings as SettingsIcon, Cpu } from 'lucide-react';
import BackendStatus from '../components/BackendStatus';

export default function RootLayout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 border-r border-slate-200 dark:border-slate-800 p-4 flex flex-col">
        <div className="font-bold text-xl mb-8 flex items-center gap-2">
          <Activity className="text-indigo-600" />
          QuantumFraud
        </div>
        
        <nav className="flex-1 space-y-2 text-sm">
          <Link to="/" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
            <LayoutDashboard size={18} /> Dashboard
          </Link>
          <Link to="/live" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
            <Activity size={18} /> Live Payments
          </Link>
          <Link to="/transactions" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
             Transactions
          </Link>
          <Link to="/models" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
             <Cpu size={18} /> AI Models
          </Link>
          <Link to="/vqc-lab" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
             VQC Lab
          </Link>
          <Link to="/settings" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
            <SettingsIcon size={18} /> Settings
          </Link>
        </nav>

        <div className="mt-auto border-t pt-4 border-slate-200 dark:border-slate-800">
           <BackendStatus />
           <button onClick={toggleTheme} className="mt-4 text-xs px-4 py-2 bg-indigo-600 text-white rounded w-full">
             Toggle Theme ({theme})
           </button>
        </div>
      </aside>

      <main className="flex-1 p-8 bg-slate-50 dark:bg-[#0f172a] h-screen overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
""")

write_file("README.md", """
# Quantum-Assisted Real-Time Payment Fraud Detection

## Phase 3: Classical AI Fraud Detection

### Dataset Setup
This project uses the PaySim dataset (Kaggle: `ealaxi/paysim1`).
Due to size, it is not tracked in Git.
To train the model:
1. Download the dataset CSV (`PS_20174392719_1491204439457_log.csv`).
2. Place it in the `/data` directory at the root of the project.

### Training the Model
```bash
cd backend
python -m app.ml.train_xgboost
```
This will:
- Read the dataset
- Split chronologically
- Train XGBoost
- Save `xgboost_fraud_model.json` and `model_metadata.json` to `/artifacts/models/`

### Prediction API
The model exposes:
- `GET /api/v1/models/xgboost/status`
- `POST /api/v1/transactions/{transaction_id}/predict`

Make sure dependencies (`xgboost`, `pandas`, `scikit-learn`) are installed.
""")

print("Phase 3 setup complete.")
