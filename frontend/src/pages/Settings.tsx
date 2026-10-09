import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useTheme } from '../hooks/useTheme';
import { StatusBadge } from '../components/StatusBadge';
import { Settings as SettingsIcon, Sun, Moon, Sliders, Shield, Cpu, Activity, RefreshCw } from 'lucide-react';

export default function Settings() {
  const { theme, toggleTheme } = useTheme();
  const [sysStatus, setSysStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/analytics/overview`);
      setSysStatus(res.data?.system_status || {});
    } catch (err) {
      console.error('Failed to fetch system status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <SettingsIcon className="text-indigo-500" size={32} /> Platform Settings & Configuration
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          System telemetry, model weights, risk threshold parameters, and interface preferences.
        </p>
      </div>

      {/* Appearance Section */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
          {theme === 'dark' ? <Moon size={20} className="text-indigo-400" /> : <Sun size={20} className="text-amber-500" />}
          Interface Theme & Appearance
        </h2>

        <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800">
          <div>
            <span className="font-semibold text-sm block">Current Mode: {theme.toUpperCase()}</span>
            <span className="text-xs text-slate-500">Toggle between Light (Slate Clean) and Dark (Deep Slate Security) themes.</span>
          </div>

          <button
            onClick={toggleTheme}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg transition shadow-sm"
          >
            Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode
          </button>
        </div>
      </div>

      {/* Read-only Hybrid Weights Configuration */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Sliders size={20} className="text-amber-500" /> Model Fusion Weights (Read-Only)
          </h2>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            Validated Configuration
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-500 block flex items-center gap-1.5">
              <Cpu size={14} className="text-indigo-500" /> Classical XGBoost Weight
            </span>
            <span className="font-mono text-2xl font-extrabold text-indigo-500">30% (0.30)</span>
            <p className="text-[11px] text-slate-400">Fixed weight selected by validation set grid search.</p>
          </div>

          <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-500 block flex items-center gap-1.5">
              <Activity size={14} className="text-fuchsia-500" /> Quantum VQC Weight
            </span>
            <span className="font-mono text-2xl font-extrabold text-fuchsia-500">70% (0.70)</span>
            <p className="text-[11px] text-slate-400">Fixed weight selected by validation set grid search.</p>
          </div>
        </div>
      </div>

      {/* Read-only Risk Decision Thresholds */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
          <Shield size={20} className="text-emerald-500" /> Business Risk Thresholds
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl border border-emerald-200 dark:border-emerald-900/50 space-y-1">
            <span className="text-xs font-bold text-emerald-800 dark:text-emerald-300 font-sans block">SAFE Decision</span>
            <span className="text-base font-extrabold text-emerald-600 dark:text-emerald-400">0.00 – &lt; 0.30</span>
            <p className="text-[11px] text-emerald-700 dark:text-emerald-400 font-sans">Low risk transaction.</p>
          </div>

          <div className="p-4 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-900/50 space-y-1">
            <span className="text-xs font-bold text-amber-800 dark:text-amber-300 font-sans block">REVIEW Decision</span>
            <span className="text-base font-extrabold text-amber-600 dark:text-amber-400">0.30 – &lt; 0.70</span>
            <p className="text-[11px] text-amber-700 dark:text-amber-400 font-sans">Manual investigation required.</p>
          </div>

          <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-xl border border-red-200 dark:border-red-900/50 space-y-1">
            <span className="text-xs font-bold text-red-800 dark:text-red-300 font-sans block">ALERT Decision</span>
            <span className="text-base font-extrabold text-red-600 dark:text-red-400">0.70 – 1.00</span>
            <p className="text-[11px] text-red-700 dark:text-red-400 font-sans">Fraud alert generated & stored.</p>
          </div>
        </div>
      </div>

      {/* System Telemetry Overview */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200">System Telemetry & Status</h2>
          <button
            onClick={fetchStatus}
            className="p-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300 transition"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <span className="text-slate-500 block font-sans text-[11px]">Backend API</span>
            <StatusBadge status={sysStatus?.backend || 'online'} />
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <span className="text-slate-500 block font-sans text-[11px]">Database</span>
            <StatusBadge status={sysStatus?.database || 'disconnected'} />
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <span className="text-slate-500 block font-sans text-[11px]">XGBoost Model</span>
            <StatusBadge status={sysStatus?.xgboost || 'unavailable'} />
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <span className="text-slate-500 block font-sans text-[11px]">Quantum VQC</span>
            <StatusBadge status={sysStatus?.vqc || 'unavailable'} />
          </div>
        </div>
      </div>
    </div>
  );
}
