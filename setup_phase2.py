import os
import textwrap

BASE_DIR = r"c:\Users\HP\OneDrive\Desktop\QUANTUM FRAUD DETECTION"

def write_file(path, content):
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 1. Update Transaction Model
write_file("backend/app/models/transaction.py", """
from sqlalchemy import Column, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_type = Column(String, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender_id = Column(String, index=True)
    receiver_id = Column(String, index=True)
    location = Column(String, nullable=True)
    status = Column(String, default="PENDING")
    is_simulated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
""")

# 2. Pydantic Schemas
write_file("backend/app/schemas/transaction.py", """
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class TransactionBase(BaseModel):
    transaction_type: str = Field(..., description="Type of transaction, e.g., TRANSFER, PAYMENT")
    amount: float = Field(..., gt=0, description="Transaction amount")
    sender_id: str
    receiver_id: str
    location: Optional[str] = None
    is_simulated: bool = False

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    transaction_id: UUID
    timestamp: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int
""")

# 3. Transaction Router
write_file("backend/app/api/v1/transactions.py", """
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, Any
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionListResponse
from app.models.transaction import Transaction
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_in: TransactionCreate
) -> Any:
    db_obj = Transaction(
        transaction_type=transaction_in.transaction_type,
        amount=transaction_in.amount,
        sender_id=transaction_in.sender_id,
        receiver_id=transaction_in.receiver_id,
        location=transaction_in.location,
        is_simulated=transaction_in.is_simulated,
        status="PENDING"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=TransactionListResponse)
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
) -> Any:
    query = db.query(Transaction)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if status:
        query = query.filter(Transaction.status == status)
    
    total = query.count()
    items = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit).all()
    
    return TransactionListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        size=limit
    )

@router.get("/{transaction_id}", response_model=TransactionResponse)
def read_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_id: str
) -> Any:
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction
""")

# Update API Router
write_file("backend/app/api/v1/__init__.py", """
from fastapi import APIRouter
from app.api.v1.transactions import router as transactions_router

router = APIRouter()
router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
""")

# Health check with DB
write_file("backend/app/main.py", """
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.api.v1 import router as api_v1_router
from app.websocket.stream import router as ws_router
from app.db.session import SessionLocal

app = FastAPI(title="Quantum Fraud Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws/v1")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass
    
    return {
        "status": "ok", 
        "service": "fraud-detection-backend",
        "database": db_status
    }
""")

# Backend Status UI
write_file("frontend/src/components/BackendStatus.tsx", """
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function BackendStatus() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await axios.get(import.meta.env.VITE_API_BASE_URL + '/health');
        if (res.data.status === 'ok') {
          setBackendStatus('connected');
        } else {
          setBackendStatus('disconnected');
        }
        
        if (res.data.database === 'connected') {
            setDbStatus('connected');
        } else {
            setDbStatus('disconnected');
        }
      } catch {
        setBackendStatus('disconnected');
        setDbStatus('disconnected');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-sm flex flex-col gap-1">
      <div className="flex items-center gap-2">
          Backend: 
          {backendStatus === 'checking' && <span className="text-yellow-500">Checking...</span>}
          {backendStatus === 'connected' && <span className="text-green-500">● Connected</span>}
          {backendStatus === 'disconnected' && <span className="text-red-500">○ Disconnected</span>}
      </div>
      <div className="flex items-center gap-2">
          Database: 
          {dbStatus === 'checking' && <span className="text-yellow-500">Checking...</span>}
          {dbStatus === 'connected' && <span className="text-green-500">● Connected</span>}
          {dbStatus === 'disconnected' && <span className="text-red-500">○ Disconnected</span>}
      </div>
    </div>
  );
}
""")

# React Transactions Explorer
write_file("frontend/src/pages/Transactions.tsx", """
import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Search, Plus } from 'lucide-react';

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await axios.get(import.meta.env.VITE_API_BASE_URL + '/transactions');
      setTransactions(res.data.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Transactions</h1>
        <Link to="/transactions/new" className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition">
          <Plus size={18} /> New Payment
        </Link>
      </div>

      <div className="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
        <div className="flex gap-4 mb-4">
           <div className="relative flex-1">
             <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
             <input type="text" placeholder="Search by ID or Sender..." className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
           </div>
           <select className="px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
             <option value="">All Types</option>
             <option value="TRANSFER">TRANSFER</option>
             <option value="PAYMENT">PAYMENT</option>
           </select>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading transactions...</div>
        ) : error ? (
          <div className="text-center py-12 text-red-500 border border-dashed border-red-200 rounded-lg">
             <p>{error}</p>
             <p className="text-sm mt-2 text-slate-400">Is the backend running and database connected?</p>
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-12 text-slate-500 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg">
            No transactions yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-sm text-slate-500">
                  <th className="pb-3 pr-4 font-medium">ID</th>
                  <th className="pb-3 pr-4 font-medium">Type</th>
                  <th className="pb-3 pr-4 font-medium">Amount</th>
                  <th className="pb-3 pr-4 font-medium">Sender</th>
                  <th className="pb-3 pr-4 font-medium">Date</th>
                  <th className="pb-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx: any) => (
                  <tr key={tx.transaction_id} className="border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                    <td className="py-3 pr-4 font-mono text-xs">
                        <Link to={`/transactions/${tx.transaction_id}`} className="text-indigo-600 dark:text-indigo-400 hover:underline">
                            {tx.transaction_id.substring(0, 8)}...
                        </Link>
                    </td>
                    <td className="py-3 pr-4"><span className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-xs rounded-md">{tx.transaction_type}</span></td>
                    <td className="py-3 pr-4 font-medium">₹{tx.amount.toLocaleString()}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{tx.sender_id}</td>
                    <td className="py-3 pr-4 text-sm text-slate-500">{new Date(tx.timestamp).toLocaleString()}</td>
                    <td className="py-3">
                        <span className={`px-2 py-1 text-xs rounded-md ${tx.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-500' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                            {tx.status}
                        </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
""")

# React New Payment Form
write_file("frontend/src/pages/NewPayment.tsx", """
import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function NewPayment() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    transaction_type: 'TRANSFER',
    amount: '',
    sender_id: '',
    receiver_id: '',
    location: '',
    is_simulated: true
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    
    try {
      const res = await axios.post(import.meta.env.VITE_API_BASE_URL + '/transactions/', {
        ...formData,
        amount: parseFloat(formData.amount)
      });
      navigate(`/transactions/${res.data.transaction_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit payment');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">New Payment</h1>
      
      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        {error && <div className="p-3 bg-red-100 text-red-700 rounded-lg text-sm">{error}</div>}
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Type</label>
            <select 
              value={formData.transaction_type}
              onChange={e => setFormData({...formData, transaction_type: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="TRANSFER">TRANSFER</option>
              <option value="PAYMENT">PAYMENT</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Amount (₹)</label>
            <input 
              type="number" required min="1" step="0.01"
              value={formData.amount}
              onChange={e => setFormData({...formData, amount: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Sender ID</label>
            <input 
              type="text" required placeholder="••••4821"
              value={formData.sender_id}
              onChange={e => setFormData({...formData, sender_id: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Receiver ID</label>
            <input 
              type="text" required placeholder="••••9017"
              value={formData.receiver_id}
              onChange={e => setFormData({...formData, receiver_id: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Location</label>
          <input 
            type="text" placeholder="e.g. Chennai"
            value={formData.location}
            onChange={e => setFormData({...formData, location: e.target.value})}
            className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
          <button 
            type="submit" 
            disabled={submitting}
            className="w-full bg-indigo-600 text-white font-medium py-3 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
          >
            {submitting ? 'Processing...' : 'Submit Payment Request'}
          </button>
        </div>
      </form>
    </div>
  );
}
""")

# React Transaction Detail
write_file("frontend/src/pages/TransactionDetail.tsx", """
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, ShieldAlert, Cpu } from 'lucide-react';

export default function TransactionDetail() {
  const { id } = useParams();
  const [tx, setTx] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTx = async () => {
      try {
        const res = await axios.get(import.meta.env.VITE_API_BASE_URL + `/transactions/${id}`);
        setTx(res.data);
      } catch (err: any) {
        setError('Transaction not found or backend unavailable');
      } finally {
        setLoading(false);
      }
    };
    fetchTx();
  }, [id]);

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
        
        {/* Core Details */}
        <div className="md:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <h2 className="text-xl font-semibold mb-4">Payment Details</h2>
          <div className="grid grid-cols-2 gap-y-4 text-sm">
            <div><span className="text-slate-500 block">Transaction ID</span><span className="font-mono">{tx.transaction_id}</span></div>
            <div><span className="text-slate-500 block">Status</span><span className="font-medium text-yellow-600">{tx.status}</span></div>
            <div><span className="text-slate-500 block">Amount</span><span className="font-medium text-lg">₹{tx.amount.toLocaleString()}</span></div>
            <div><span className="text-slate-500 block">Type</span><span>{tx.transaction_type}</span></div>
            <div><span className="text-slate-500 block">Sender</span><span className="font-mono">{tx.sender_id}</span></div>
            <div><span className="text-slate-500 block">Receiver</span><span className="font-mono">{tx.receiver_id}</span></div>
            <div><span className="text-slate-500 block">Location</span><span>{tx.location || 'N/A'}</span></div>
            <div><span className="text-slate-500 block">Timestamp</span><span>{new Date(tx.timestamp).toLocaleString()}</span></div>
            <div><span className="text-slate-500 block">Simulated</span><span>{tx.is_simulated ? 'Yes' : 'No'}</span></div>
          </div>
        </div>

        {/* AI Analysis Panel */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
             <div className="flex items-center gap-2 mb-4 text-slate-700 dark:text-slate-300">
                 <Cpu size={20} className="text-indigo-500" /> 
                 <h2 className="text-lg font-semibold">Classical AI</h2>
             </div>
             <p className="text-slate-500 text-sm italic">Not evaluated yet</p>
          </div>

          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
             <div className="flex items-center gap-2 mb-4 text-slate-700 dark:text-slate-300">
                 <ShieldAlert size={20} className="text-fuchsia-500" /> 
                 <h2 className="text-lg font-semibold">Quantum AI (VQC)</h2>
             </div>
             <p className="text-slate-500 text-sm italic">Not evaluated yet</p>
          </div>

          <div className="bg-gradient-to-br from-indigo-600 to-fuchsia-600 p-[1px] rounded-xl shadow-sm">
             <div className="bg-white dark:bg-slate-900 p-6 rounded-xl h-full w-full">
                 <h2 className="text-lg font-semibold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-fuchsia-500">Hybrid Risk Engine</h2>
                 <p className="text-slate-500 text-sm italic">Pending Phase 3 Integration</p>
             </div>
          </div>
        </div>

      </div>
    </div>
  );
}
""")

# App.tsx Routes Update
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
          <Route path="models" element={<EmptyStatePage title="AI Models" />} />
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

print("Phase 2 setup complete.")
