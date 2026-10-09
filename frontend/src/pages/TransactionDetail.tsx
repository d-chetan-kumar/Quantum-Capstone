import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { ArrowLeft, Cpu, Activity, Zap, CheckCircle2, AlertTriangle, AlertOctagon, User, UserCheck } from 'lucide-react';
import { formatISTDate } from '../utils/dateUtils';


export default function TransactionDetail() {
  const { id } = useParams();
  const [tx, setTx] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [quantumPrediction, setQuantumPrediction] = useState<any>(null);
  const [riskPrediction, setRiskPrediction] = useState<any>(null);
  const [behaviour, setBehaviour] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [analyzing, setAnalyzing] = useState(false);
  const [quantumAnalyzing, setQuantumAnalyzing] = useState(false);
  const [riskAnalyzing, setRiskAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const [xgbError, setXgbError] = useState('');
  const [quantumError, setQuantumError] = useState('');
  const [riskError, setRiskError] = useState('');

  useEffect(() => {
    const fetchTx = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/transactions/${id}`);
        setTx(res.data);
        
        try {
          const riskRes = await axios.get(`${API_BASE_URL}/transactions/${id}/risk`);
          setRiskPrediction(riskRes.data);
          if (riskRes.data.classical_probability !== undefined) {
            setPrediction({
              fraud_probability: riskRes.data.classical_probability,
              predicted_class: riskRes.data.classical_probability > 0.5 ? 1 : 0
            });
          }
          if (riskRes.data.quantum_probability !== undefined) {
            setQuantumPrediction({
              fraud_probability: riskRes.data.quantum_probability,
              predicted_class: riskRes.data.quantum_probability > 0.5 ? 1 : 0
            });
          }
        } catch (e) {
          try {
            const predRes = await axios.get(`${API_BASE_URL}/transactions/${id}/predict`);
            if (predRes.data.model_name === 'vqc') {
              setQuantumPrediction(predRes.data);
            } else if (predRes.data.model_name === 'hybrid') {
              setRiskPrediction(predRes.data);
            } else {
              setPrediction(predRes.data);
            }
          } catch (err) {
            // No prediction stored yet
          }
        }

        try {
          const bRes = await axios.get(`${API_BASE_URL}/transactions/${id}/behaviour`);
          setBehaviour(bRes.data);
        } catch (e) {
          // Behavioural risk unavailable
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
    setXgbError('');
    try {
        const res = await axios.post(`${API_BASE_URL}/transactions/${id}/predict`);
        setPrediction(res.data);
    } catch (err: any) {
        setXgbError(err.response?.data?.detail || "Failed to run XGBoost analysis.");
    } finally {
        setAnalyzing(false);
    }
  };

  const handleQuantumPredict = async () => {
    setQuantumAnalyzing(true);
    setQuantumError('');
    try {
        const res = await axios.post(`${API_BASE_URL}/transactions/${id}/quantum-predict`);
        setQuantumPrediction(res.data);
    } catch (err: any) {
        setQuantumError(err.response?.data?.detail || "Quantum VQC model unavailable.");
    } finally {
        setQuantumAnalyzing(false);
    }
  };

  const handleRiskPredict = async () => {
    setRiskAnalyzing(true);
    setRiskError('');
    try {
        const res = await axios.post(`${API_BASE_URL}/transactions/${id}/risk`);
        setRiskPrediction(res.data);
    } catch (err: any) {
        setRiskError(err.response?.data?.detail || "Hybrid risk engine unavailable.");
    } finally {
        setRiskAnalyzing(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading payment details...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  const getRiskBadge = (level: string) => {
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
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/transactions" className="p-2 bg-slate-200 dark:bg-slate-800 rounded-full hover:bg-slate-300 dark:hover:bg-slate-700 transition">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Transaction Investigation</h1>
            <span className="font-mono text-xs text-indigo-600 dark:text-indigo-400 font-semibold block mt-0.5">
              ID: {tx.transaction_id}
            </span>
          </div>
        </div>
        {riskPrediction?.risk_level && getRiskBadge(riskPrediction.risk_level)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Payment Information */}
        <div className="lg:col-span-1 bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <h2 className="text-xl font-semibold mb-4">Payment Details</h2>
          <div className="space-y-4 text-sm">
            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
              <span className="text-slate-500 block text-[11px] font-medium">Transaction ID</span>
              <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400 break-all select-all">{tx.transaction_id}</span>
            </div>
            <div><span className="text-slate-500 block text-xs">Status</span><span className="font-semibold text-emerald-600 dark:text-emerald-400">{tx.status}</span></div>
            <div><span className="text-slate-500 block text-xs">Amount</span><span className="font-bold text-2xl text-slate-900 dark:text-white">₹{tx.amount.toLocaleString()}</span></div>
            <div><span className="text-slate-500 block text-xs">Transaction Type</span><span className="font-semibold">{tx.transaction_type}</span></div>
            <div><span className="text-slate-500 block text-xs">Sender ID</span><span className="font-mono text-xs font-medium">{tx.sender_id}</span></div>
            <div><span className="text-slate-500 block text-xs">Receiver ID</span><span className="font-mono text-xs font-medium">{tx.receiver_id}</span></div>
            <div><span className="text-slate-500 block text-xs">Timestamp</span><span className="text-xs font-mono">{formatISTDate(tx.timestamp || tx.created_at)}</span></div>
          </div>
        </div>

        {/* AI Model Analyses */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* XGBoost Analysis */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
               <div className="flex items-center gap-2 mb-4 text-slate-700 dark:text-slate-300">
                   <Cpu size={20} className="text-indigo-500" /> 
                   <h2 className="text-lg font-semibold">Classical XGBoost</h2>
               </div>
               
               {analyzing ? (
                   <p className="text-indigo-500 text-sm animate-pulse">Running XGBoost analysis...</p>
               ) : xgbError ? (
                   <div className="space-y-3">
                       <p className="text-red-500 text-xs font-medium bg-red-50 dark:bg-red-950/40 p-2.5 rounded-lg border border-red-200 dark:border-red-900/50">{xgbError}</p>
                       <button onClick={handlePredict} className="w-full py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition text-xs">
                           Retry XGBoost Analysis
                       </button>
                   </div>
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
                   </div>
               ) : (
                   <div className="text-center">
                      <p className="text-slate-500 text-sm italic mb-4">Not evaluated yet</p>
                      <button onClick={handlePredict} className="w-full py-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition text-xs">
                          Run XGBoost Analysis
                      </button>
                   </div>
               )}
            </div>

            {/* Quantum VQC Analysis */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
               <div className="flex items-center gap-2 mb-4 text-slate-700 dark:text-slate-300">
                   <Activity size={20} className="text-fuchsia-500" /> 
                   <h2 className="text-lg font-semibold">Quantum VQC</h2>
               </div>
               
               {quantumAnalyzing ? (
                   <p className="text-fuchsia-500 text-sm animate-pulse">Running quantum analysis...</p>
               ) : quantumError ? (
                   <div className="space-y-3">
                       <p className="text-red-500 text-xs font-medium bg-red-50 dark:bg-red-950/40 p-2.5 rounded-lg border border-red-200 dark:border-red-900/50">{quantumError}</p>
                       <button onClick={handleQuantumPredict} className="w-full py-2 bg-fuchsia-600 text-white font-medium rounded-lg hover:bg-fuchsia-700 transition text-xs">
                           Retry Quantum Analysis
                       </button>
                   </div>
               ) : quantumPrediction ? (
                   <div className="space-y-3 text-sm">
                      <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                          <span className="text-slate-500">Quantum Fraud Probability</span>
                          <span className={`font-bold text-lg ${quantumPrediction.fraud_probability > 0.5 ? 'text-red-500' : 'text-green-500'}`}>
                              {(quantumPrediction.fraud_probability * 100).toFixed(1)}%
                          </span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                          <span className="text-slate-500">Predicted Class</span>
                          <span className="font-medium">{quantumPrediction.predicted_class === 1 ? 'FRAUD' : 'LEGITIMATE'}</span>
                      </div>
                   </div>
               ) : (
                   <div className="text-center">
                      <p className="text-slate-500 text-sm italic mb-4">Quantum analysis not performed</p>
                      <button onClick={handleQuantumPredict} className="w-full py-2 bg-fuchsia-50 dark:bg-fuchsia-900/30 text-fuchsia-600 dark:text-fuchsia-400 font-medium rounded-lg hover:bg-fuchsia-100 dark:hover:bg-fuchsia-900/50 transition text-xs">
                          Run Quantum Analysis
                      </button>
                   </div>
               )}
            </div>

          </div>

          {/* Hybrid Risk Analysis Card */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-amber-200 dark:border-amber-900/50 space-y-4">
             <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Zap size={22} className="text-amber-500" />
                    <h2 className="text-xl font-bold">Hybrid Risk Engine Decision</h2>
                </div>
                {riskPrediction && getRiskBadge(riskPrediction.risk_level)}
             </div>

             {riskAnalyzing ? (
                 <p className="text-amber-500 text-sm animate-pulse">Computing hybrid risk score...</p>
             ) : riskError ? (
                 <div className="space-y-3">
                     <p className="text-red-500 text-xs font-medium bg-red-50 dark:bg-red-950/40 p-2.5 rounded-lg border border-red-200 dark:border-red-900/50">{riskError}</p>
                     <button onClick={handleRiskPredict} className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-lg shadow-sm transition text-sm">
                         Retry Hybrid Risk Analysis
                     </button>
                 </div>
             ) : riskPrediction ? (
                 <div className="space-y-4 text-sm">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                       <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                          <span className="text-slate-500 text-xs block">Classical Prob (30%)</span>
                          <span className="font-mono font-semibold text-indigo-500">
                             {(riskPrediction.classical_probability * 100).toFixed(1)}%
                          </span>
                       </div>
                       <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                          <span className="text-slate-500 text-xs block">Quantum Prob (70%)</span>
                          <span className="font-mono font-semibold text-fuchsia-500">
                             {(riskPrediction.quantum_probability * 100).toFixed(1)}%
                          </span>
                       </div>
                       <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 rounded-lg">
                          <span className="text-amber-800 dark:text-amber-300 text-xs block font-medium">Hybrid Risk Score</span>
                          <span className="font-mono font-bold text-xl text-amber-600 dark:text-amber-400">
                             {(riskPrediction.hybrid_probability * 100).toFixed(1)}%
                          </span>
                       </div>
                    </div>

                    <div className="text-xs text-slate-400 border-t border-slate-200 dark:border-slate-800 pt-3">
                       Evaluated by Risk Engine v1.0 | Timestamp: {formatISTDate(riskPrediction.created_at)}
                    </div>
                 </div>
             ) : (
                 <div className="text-center py-2">
                    <p className="text-slate-500 text-sm italic mb-4">Combine XGBoost (30%) + VQC (70%) for unified risk decision</p>
                    <button
                        onClick={handleRiskPredict}
                        className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-lg shadow-sm transition text-sm"
                    >
                        Execute Hybrid Risk Analysis
                    </button>
                 </div>
             )}
          </div>

          {/* Account Discovery & Behavioural Risk Analysis Card */}
          {behaviour && (
            <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-indigo-200 dark:border-indigo-900/50 space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <UserCheck size={22} className="text-indigo-500" />
                  <h2 className="text-xl font-bold">Account Discovery & Behavioural Risk</h2>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                  behaviour.behavioural_risk_signal === 'SUSPICIOUS' ? 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400' :
                  behaviour.behavioural_risk_signal === 'ELEVATED' ? 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400' :
                  behaviour.behavioural_risk_signal === 'INSUFFICIENT_DATA' ? 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300' :
                  'bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400'
                }`}>
                  Signal: {behaviour.behavioural_risk_signal}
                </span>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-800 font-medium">
                {behaviour.summary}
              </p>

              {/* Sender vs Receiver Discovery Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                {/* Sender Profile */}
                <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 space-y-2">
                  <div className="flex justify-between items-center pb-2 border-b border-slate-200 dark:border-slate-700">
                    <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1">
                      <User size={14} className="text-indigo-500" /> Sender: {behaviour.sender?.account_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${behaviour.sender?.is_known ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'}`}>
                      {behaviour.sender?.is_known ? 'Known Account' : 'Newly Observed'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                    <div><span className="text-slate-500 block text-[10px] font-sans">History Status</span><span className="font-semibold">{behaviour.sender?.history_status}</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Previous Sent</span><span className="font-bold">{behaviour.sender?.previous_tx_count}</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Avg Sent Amount</span><span className="font-semibold">₹{behaviour.sender?.avg_sent_amount?.toLocaleString() || '0'}</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Deviation Ratio</span><span className="font-bold text-indigo-500">{behaviour.sender?.amount_deviation_ratio}x</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Distinct Recipients</span><span>{behaviour.sender?.distinct_recipients_count}</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Recent 24h Count</span><span>{behaviour.sender?.recent_24h_tx_count}</span></div>
                  </div>
                </div>

                {/* Receiver Profile */}
                <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 space-y-2">
                  <div className="flex justify-between items-center pb-2 border-b border-slate-200 dark:border-slate-700">
                    <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1">
                      <User size={14} className="text-fuchsia-500" /> Receiver: {behaviour.receiver?.account_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${behaviour.receiver?.is_known ? 'bg-fuchsia-100 text-fuchsia-800 dark:bg-fuchsia-900/40 dark:text-fuchsia-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'}`}>
                      {behaviour.receiver?.is_known ? 'Known Account' : 'Newly Observed'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                    <div><span className="text-slate-500 block text-[10px] font-sans">History Status</span><span className="font-semibold">{behaviour.receiver?.history_status}</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Previous Received</span><span className="font-bold">{behaviour.receiver?.previous_received_count}</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Avg Received Amount</span><span className="font-semibold">₹{behaviour.receiver?.avg_received_amount?.toLocaleString() || '0'}</span></div>
                    <div><span className="text-slate-500 block text-[10px] font-sans">Fraud Alerts</span><span className={`font-bold ${behaviour.receiver?.verified_alerts_count > 0 ? 'text-red-500' : 'text-emerald-500'}`}>{behaviour.receiver?.verified_alerts_count || 0}</span></div>
                  </div>
                </div>
              </div>

              {/* Indicators List */}
              {behaviour.indicators && behaviour.indicators.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300 block uppercase tracking-wider">
                    Observed Behavioural Indicators
                  </span>
                  <div className="space-y-2">
                    {behaviour.indicators.map((ind: any, i: number) => (
                      <div key={i} className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg flex items-start gap-3 text-xs border border-slate-200/60 dark:border-slate-700/60">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase shrink-0 ${
                          ind.type === 'VERIFIED_EVIDENCE' ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300 border border-red-300' :
                          ind.type === 'HEURISTIC_INDICATOR' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300' :
                          'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                        }`}>
                          {ind.type === 'VERIFIED_EVIDENCE' ? 'VERIFIED EVIDENCE' : ind.type === 'HEURISTIC_INDICATOR' ? 'HEURISTIC' : 'OBSERVATION'}
                        </span>
                        <div className="space-y-0.5">
                          <span className="font-bold text-slate-800 dark:text-slate-200 block">{ind.title}</span>
                          <p className="text-slate-500 dark:text-slate-400 text-[11px]">{ind.explanation}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

