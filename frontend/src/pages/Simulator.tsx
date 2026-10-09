import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { Send, CheckCircle2, AlertTriangle, AlertOctagon, Cpu, Activity, Zap, ExternalLink } from 'lucide-react';

export default function Simulator() {
  const [amount, setAmount] = useState<number>(25000);
  const [txType, setTxType] = useState<string>('TRANSFER');
  const [senderId, setSenderId] = useState<string>('');
  const [receiverId, setReceiverId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string>('');

  const handleProcessPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);

    const s = senderId.trim();
    const r = receiverId.trim();

    if (s && r && s === r) {
      setError('Sender ID and Receiver ID cannot be identical.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        amount: Number(amount),
        transaction_type: txType,
        sender_id: s || undefined,
        receiver_id: r || undefined
      };

      const res = await axios.post(`${API_BASE_URL}/simulator/payment`, payload);
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process payment');
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadge = (level: string) => {
    switch (level) {
      case 'SAFE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 size={14} /> SAFE
          </span>
        );
      case 'REVIEW':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
            <AlertTriangle size={14} /> REVIEW REQUIRED
          </span>
        );
      case 'ALERT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800 animate-pulse">
            <AlertOctagon size={14} /> FRAUD ALERT
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold">Payment Gateway Simulator</h1>
        <p className="text-slate-500 text-sm mt-1">
          Submit real payments into the hybrid quantum-classical fraud detection pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Payment Submission Form */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Send className="text-indigo-500" size={20} /> Payment Parameters
          </h2>

          <form onSubmit={handleProcessPayment} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                Amount (INR) *
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-slate-400 font-bold">₹</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={amount}
                  onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                  className="w-full pl-8 pr-4 py-2 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 rounded-lg text-slate-900 dark:text-white font-mono font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                Transaction Type *
              </label>
              <select
                value={txType}
                onChange={(e) => setTxType(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 rounded-lg text-slate-900 dark:text-white font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="TRANSFER">TRANSFER (High Risk)</option>
                <option value="CASH_OUT">CASH_OUT (High Risk)</option>
                <option value="PAYMENT">PAYMENT</option>
                <option value="CASH_IN">CASH_IN</option>
                <option value="DEBIT">DEBIT</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                Sender ID (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. C12345678"
                value={senderId}
                onChange={(e) => setSenderId(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 rounded-lg text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                Receiver ID (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. C98765432"
                value={receiverId}
                onChange={(e) => setReceiverId(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 rounded-lg text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 text-xs rounded-lg border border-red-200 dark:border-red-900">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow-md hover:shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                  Processing Payment...
                </>
              ) : (
                <>
                  <Send size={18} /> PROCESS PAYMENT
                </>
              )}
            </button>
          </form>
        </div>

        {/* Real-time Payment Result Display */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
          <h2 className="text-xl font-bold flex items-center justify-between">
            <span>Transaction Result</span>
            {result && getDecisionBadge(result.risk_level)}
          </h2>

          {!result ? (
            <div className="h-64 flex flex-col items-center justify-center text-center p-6 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl text-slate-400">
              <Zap size={36} className="mb-2 opacity-50" />
              <p className="text-sm font-medium">Ready for input</p>
              <p className="text-xs text-slate-500 max-w-xs mt-1">
                Fill out the payment parameters and click "Process Payment" to execute classical and quantum fraud models.
              </p>
            </div>
          ) : (
            <div className="space-y-4 text-sm">
              <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl space-y-2 text-xs">
                <div className="pb-2 border-b border-slate-200 dark:border-slate-700">
                  <span className="text-slate-500 font-medium block mb-1">Transaction ID</span>
                  <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400 text-xs break-all select-all bg-indigo-50 dark:bg-indigo-950/60 px-2 py-1 rounded border border-indigo-200 dark:border-indigo-900/50 block">
                    {result.transaction_id}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 font-mono">
                  <div>
                    <span className="text-slate-500 font-sans block text-[11px]">Sender ID</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{result.sender_id || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 font-sans block text-[11px]">Receiver ID</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{result.receiver_id || 'N/A'}</span>
                  </div>
                </div>
                <div className="flex justify-between font-mono pt-1">
                  <span className="text-slate-500 font-sans">Amount</span>
                  <span className="font-bold text-slate-900 dark:text-white text-sm">₹{result.amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-slate-500 font-sans">Type</span>
                  <span className="font-semibold">{result.transaction_type}</span>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-slate-500 font-sans">Timestamp</span>
                  <span className="text-slate-600 dark:text-slate-300 text-[11px]">{result.created_at ? new Date(result.created_at).toLocaleString() : new Date().toLocaleString()}</span>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-slate-500 font-sans">Processing Time</span>
                  <span className="text-indigo-600 dark:text-indigo-400 font-bold">{result.processing_time_ms} ms</span>
                </div>
              </div>

              {/* Model Probabilities */}
              <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between p-2.5 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 text-xs flex items-center gap-1.5 font-medium">
                    <Cpu size={14} className="text-indigo-500" /> XGBoost Risk (30%)
                  </span>
                  <span className="font-mono font-bold text-indigo-500">
                    {(result.classical_probability * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 text-xs flex items-center gap-1.5 font-medium">
                    <Activity size={14} className="text-fuchsia-500" /> VQC Risk (70%)
                  </span>
                  <span className="font-mono font-bold text-fuchsia-500">
                    {(result.quantum_probability * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 rounded-lg">
                  <span className="text-amber-900 dark:text-amber-300 font-bold text-xs flex items-center gap-1.5">
                    <Zap size={14} className="text-amber-500" /> Hybrid Fraud Score
                  </span>
                  <span className="font-mono font-extrabold text-lg text-amber-600 dark:text-amber-400">
                    {(result.hybrid_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="pt-2 flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  {result.persisted ? 'Persisted to DB' : 'Development Mode'}
                </span>
                <Link
                  to={`/transactions/${result.transaction_id}`}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
                >
                  View Full Investigation <ExternalLink size={12} />
                </Link>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
