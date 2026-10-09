import { useState } from 'react';
import { Link } from 'react-router-dom';
import { usePaymentWebSocket, type PaymentEvent } from '../hooks/usePaymentWebSocket';
import { Radio, ShieldAlert, Cpu, Activity, Zap, CheckCircle2, AlertTriangle, AlertOctagon, ExternalLink, RefreshCw } from 'lucide-react';
import { formatISTDate, formatISTTimeOnly } from '../utils/dateUtils';


export default function LivePayments() {
  const { status, events, latestAlert, clearEvents } = usePaymentWebSocket();
  const [selectedPayment, setSelectedPayment] = useState<PaymentEvent | null>(null);

  // Compute live metrics from received WebSocket events
  const safeCount = events.filter((e) => e.risk_level === 'SAFE').length;
  const reviewCount = events.filter((e) => e.risk_level === 'REVIEW').length;
  const alertCount = events.filter((e) => e.risk_level === 'ALERT').length;

  const getDecisionBadge = (level: string) => {
    switch (level) {
      case 'SAFE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 size={12} /> SAFE
          </span>
        );
      case 'REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
            <AlertTriangle size={12} /> REVIEW
          </span>
        );
      case 'ALERT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800 animate-pulse">
            <AlertOctagon size={12} /> ALERT
          </span>
        );
      default:
        return null;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'CONNECTED':
        return (
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span> WebSocket Connected
          </span>
        );
      case 'CONNECTING':
        return (
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            <RefreshCw size={12} className="animate-spin" /> Connecting to stream...
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
            Disconnected / Reconnecting
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Radio className="text-indigo-500" size={32} /> Live Payment Monitor
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Real-time WebSocket event stream evaluated by classical XGBoost and Quantum VQC models.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {getStatusBadge()}
          {events.length > 0 && (
            <button
              onClick={clearEvents}
              className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg text-xs font-medium transition"
            >
              Clear Stream
            </button>
          )}
        </div>
      </div>

      {/* Real-time Alert Banner if ALERT event arrives */}
      {latestAlert && (
        <div className="bg-red-50 dark:bg-red-950/50 border-2 border-red-500/50 p-4 rounded-xl flex items-center justify-between shadow-lg animate-pulse">
          <div className="flex items-center gap-3">
            <ShieldAlert size={28} className="text-red-600 dark:text-red-400" />
            <div>
              <h3 className="font-bold text-red-900 dark:text-red-200 text-sm">CRITICAL FRAUD RISK ALERT DETECTED</h3>
              <p className="text-xs text-red-700 dark:text-red-300">
                Transaction ID <span className="font-mono">{latestAlert.transaction_id.slice(0, 12)}...</span> triggered an ALERT with a hybrid risk score of <span className="font-bold">{(latestAlert.hybrid_probability * 100).toFixed(1)}%</span>.
              </p>
            </div>
          </div>
          <Link
            to={`/transactions/${latestAlert.transaction_id}`}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg text-xs transition shadow"
          >
            Investigate Alert
          </Link>
        </div>
      )}

      {/* Top KPI Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-slate-500 text-xs font-semibold uppercase block">Live Payments</span>
          <span className="text-2xl font-bold text-slate-900 dark:text-white font-mono">{events.length}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-emerald-600 dark:text-emerald-400 text-xs font-semibold uppercase block">Safe Decisions</span>
          <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">{safeCount}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-amber-600 dark:text-amber-400 text-xs font-semibold uppercase block">Review Decisions</span>
          <span className="text-2xl font-bold text-amber-600 dark:text-amber-400 font-mono">{reviewCount}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-red-600 dark:text-red-400 text-xs font-semibold uppercase block">Alert Decisions</span>
          <span className="text-2xl font-bold text-red-600 dark:text-red-400 font-mono">{alertCount}</span>
        </div>
      </div>

      {/* Main Grid: Stream + Inspector Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Live Payment Stream */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/50">
            <h2 className="font-bold text-sm uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Live Stream Feed
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              {events.length > 0 ? `Showing newest ${events.length} events` : 'Waiting for events'}
            </span>
          </div>

          {events.length === 0 ? (
            <div className="p-16 text-center text-slate-400 space-y-2">
              <Radio size={36} className="mx-auto opacity-40 animate-pulse text-indigo-500" />
              <p className="font-semibold text-slate-600 dark:text-slate-300 text-sm">Waiting for live payment events</p>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Open the <Link to="/simulator" className="text-indigo-500 underline font-semibold">Payment Simulator</Link> in another tab to submit transactions and see real-time events streamed here via WebSocket.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-800/40 text-slate-500 uppercase text-[11px] border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Transaction ID</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Hybrid Score</th>
                    <th className="px-4 py-3">Decision</th>
                    <th className="px-4 py-3 text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-xs">
                  {events.map((e) => (
                    <tr
                      key={e.transaction_id}
                      onClick={() => setSelectedPayment(e)}
                      className={`cursor-pointer transition hover:bg-slate-50 dark:hover:bg-slate-800/50 ${selectedPayment?.transaction_id === e.transaction_id ? 'bg-indigo-50/70 dark:bg-indigo-950/40' : ''}`}
                    >
                      <td className="px-4 py-3 font-semibold text-indigo-600 dark:text-indigo-400">
                        <Link
                          to={`/transactions/${e.transaction_id}`}
                          className="hover:underline flex items-center gap-1 font-mono text-xs"
                          onClick={(evt) => evt.stopPropagation()}
                        >
                          {e.transaction_id.slice(0, 12)}... <ExternalLink size={10} />
                        </Link>
                      </td>
                      <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">
                        ₹{e.amount.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 font-sans font-medium text-slate-600 dark:text-slate-400">
                        {e.transaction_type}
                      </td>
                      <td className="px-4 py-3 font-bold text-amber-600 dark:text-amber-400">
                        {(e.hybrid_probability * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 font-sans">
                        {getDecisionBadge(e.risk_level)}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-400 font-sans text-[11px]">
                        {formatISTTimeOnly(e.timestamp)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Payment Detail Sidebar */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
          <h2 className="text-lg font-bold flex items-center justify-between text-slate-800 dark:text-slate-200">
            <span>Selected Payment Details</span>
            {selectedPayment && getDecisionBadge(selectedPayment.risk_level)}
          </h2>

          {!selectedPayment ? (
            <div className="h-64 flex items-center justify-center text-center p-6 text-slate-400 text-xs italic border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
              Click any payment row in the live stream to inspect classical and quantum risk components.
            </div>
          ) : (
            <div className="space-y-4 text-sm">
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg space-y-1">
                <span className="text-[11px] text-slate-500 font-medium block">Transaction ID</span>
                <Link
                  to={`/transactions/${selectedPayment.transaction_id}`}
                  className="font-mono font-bold text-indigo-600 dark:text-indigo-400 text-xs break-all hover:underline block"
                >
                  {selectedPayment.transaction_id}
                </Link>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Amount</span>
                  <span className="font-bold text-slate-900 dark:text-white text-sm">₹{selectedPayment.amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Transaction Type</span>
                  <span className="font-semibold">{selectedPayment.transaction_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Sender ID</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedPayment.sender_id || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Receiver ID</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedPayment.receiver_id || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Timestamp</span>
                  <span className="text-slate-600 dark:text-slate-300 text-[11px] font-mono">{formatISTDate(selectedPayment.timestamp)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-sans">Processing Latency</span>
                  <span className="font-bold text-indigo-500">{selectedPayment.processing_time_ms} ms</span>
                </div>
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-200 dark:border-slate-800">
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded-lg flex justify-between items-center text-xs">
                  <span className="text-slate-500 flex items-center gap-1">
                    <Cpu size={14} className="text-indigo-500" /> XGBoost Risk (30%)
                  </span>
                  <span className="font-mono font-bold text-indigo-500">
                    {(selectedPayment.classical_probability * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded-lg flex justify-between items-center text-xs">
                  <span className="text-slate-500 flex items-center gap-1">
                    <Activity size={14} className="text-fuchsia-500" /> VQC Risk (70%)
                  </span>
                  <span className="font-mono font-bold text-fuchsia-500">
                    {(selectedPayment.quantum_probability * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 rounded-lg flex justify-between items-center">
                  <span className="text-amber-900 dark:text-amber-300 font-bold text-xs flex items-center gap-1">
                    <Zap size={14} className="text-amber-500" /> Hybrid Fraud Score
                  </span>
                  <span className="font-mono font-bold text-lg text-amber-600 dark:text-amber-400">
                    {(selectedPayment.hybrid_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <Link
                  to={`/transactions/${selectedPayment.transaction_id}`}
                  className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg transition flex items-center justify-center gap-1.5 text-xs shadow-sm"
                >
                  Inspect Full Details <ExternalLink size={12} />
                </Link>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
