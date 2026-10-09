import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import { ShieldCheck, Cpu, Activity, Zap, ExternalLink, RefreshCw, CreditCard } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/analytics/overview`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch dashboard overview:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 space-y-2">
        <RefreshCw className="animate-spin mx-auto text-indigo-500" size={28} />
        <p className="font-medium text-sm">Loading QuantumFraud platform overview...</p>
      </div>
    );
  }

  const sys = data?.system_status || {};
  const stats = data?.transaction_stats || {};
  const evalData = data?.hybrid_evaluation || {};
  const recentTxs = stats.recent_transactions || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Platform Overview</h1>
          <p className="text-slate-500 text-sm mt-1">
            Real-time payment authentication and hybrid quantum-classical fraud risk monitoring.
          </p>
        </div>

        {/* System Status Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={sys.backend || 'online'} label="Backend" />
          <StatusBadge status={sys.database || 'disconnected'} label="Database" />
          <StatusBadge status={sys.xgboost || 'unavailable'} label="XGBoost" />
          <StatusBadge status={sys.vqc || 'unavailable'} label="VQC 4-Qubit" />
          <StatusBadge status={sys.hybrid || 'unavailable'} label="Hybrid Engine" />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Transactions"
          value={stats.total_transactions > 0 ? stats.total_transactions : 'No data'}
          subtitle={stats.total_transactions > 0 ? 'Persisted database records' : 'No payment records yet'}
          icon={CreditCard}
          accentColor="text-indigo-500"
        />

        <MetricCard
          title="Hybrid Model Recall"
          value={evalData?.models?.hybrid ? `${(evalData.models.hybrid.recall * 100).toFixed(1)}%` : 'N/A'}
          subtitle="Evaluated on Common Test Subset"
          icon={ShieldCheck}
          accentColor="text-emerald-500"
        />

        <MetricCard
          title="Optimal Weights"
          value="30% / 70%"
          subtitle="30% XGBoost + 70% VQC"
          icon={Zap}
          accentColor="text-amber-500"
        />

        <MetricCard
          title="Quantum Architecture"
          value="4 Qubits"
          subtitle="ZZFeatureMap + RealAmplitudes"
          icon={Activity}
          accentColor="text-fuchsia-500"
        />
      </div>

      {/* Main Grid: Recent Transactions + Model Status Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recent Transactions Table */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200">Recent Payment Activity</h2>
            <Link to="/transactions" className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">
              View All Transactions →
            </Link>
          </div>

          {recentTxs.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
              <CreditCard size={32} className="mx-auto text-slate-300 dark:text-slate-700" />
              <p className="font-semibold text-sm">No payment data available</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Submit a transaction via the <Link to="/simulator" className="text-indigo-500 underline font-medium">Simulator</Link> or watch the <Link to="/live" className="text-indigo-500 underline font-medium">Live Payment Monitor</Link>.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-800/40 text-slate-500 uppercase text-[11px] border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3 py-2.5">Transaction ID</th>
                    <th className="px-3 py-2.5">Amount</th>
                    <th className="px-3 py-2.5">Type</th>
                    <th className="px-3 py-2.5">Status</th>
                    <th className="px-3 py-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-xs">
                  {recentTxs.map((t: any) => (
                    <tr key={t.transaction_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                      <td className="px-3 py-3 font-semibold text-indigo-600 dark:text-indigo-400">
                        <Link to={`/transactions/${t.transaction_id}`} className="hover:underline flex items-center gap-1 font-mono text-xs">
                          {t.transaction_id.slice(0, 12)}... <ExternalLink size={10} />
                        </Link>
                      </td>
                      <td className="px-3 py-3 font-bold text-slate-900 dark:text-white">
                        ₹{t.amount.toLocaleString()}
                      </td>
                      <td className="px-3 py-3 font-sans font-medium text-slate-600 dark:text-slate-400">
                        {t.transaction_type}
                      </td>
                      <td className="px-3 py-3 font-sans">
                        <span className="text-emerald-600 dark:text-emerald-400 font-medium text-xs">
                          {t.status}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-right font-sans">
                        <Link
                          to={`/transactions/${t.transaction_id}`}
                          className="text-indigo-600 dark:text-indigo-400 hover:underline text-xs inline-flex items-center gap-1 font-semibold"
                        >
                          Inspect <ExternalLink size={12} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Model Portfolio Overview Sidebar */}
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-4">
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Cpu size={20} className="text-indigo-500" /> Active Models
          </h2>

          <div className="space-y-3 text-sm">
            <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">XGBoost (Classical)</span>
                <StatusBadge status={sys.xgboost || 'unavailable'} />
              </div>
              <p className="text-[11px] text-slate-500">8 features extracted from PaySim schema.</p>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">VQC (Quantum AI)</span>
                <StatusBadge status={sys.vqc || 'unavailable'} />
              </div>
              <p className="text-[11px] text-slate-500">4 qubits, ZZFeatureMap + RealAmplitudes.</p>
            </div>

            <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-900/50 space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-bold text-xs text-amber-900 dark:text-amber-300">Hybrid Risk Engine</span>
                <StatusBadge status={sys.hybrid || 'unavailable'} />
              </div>
              <p className="text-[11px] text-amber-700 dark:text-amber-400">
                Weights: 30% XGB + 70% VQC (Validation F1 Optimized).
              </p>
            </div>
          </div>

          <div className="pt-2">
            <Link
              to="/models"
              className="w-full py-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg text-xs font-semibold hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition flex items-center justify-center gap-1"
            >
              Explore Full AI Portfolio →
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
