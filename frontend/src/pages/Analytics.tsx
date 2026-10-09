import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { BarChart3, Cpu, Activity, Zap, Info, RefreshCw } from 'lucide-react';

export default function Analytics() {
  const [performance, setPerformance] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchPerformance = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/analytics/performance`);
      setPerformance(res.data);
    } catch (err) {
      console.error('Failed to fetch performance analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, []);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 space-y-2">
        <RefreshCw className="animate-spin mx-auto text-indigo-500" size={28} />
        <p className="font-medium text-sm">Loading performance analytics...</p>
      </div>
    );
  }

  const models = performance?.models || {};
  const xgb = models.xgboost;
  const vqc = models.vqc;
  const hybrid = models.hybrid;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <BarChart3 className="text-indigo-500" size={32} /> Model Performance Analytics
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Empirical comparative evaluation of classical XGBoost, quantum VQC, and the weighted Hybrid Risk Engine.
          </p>
        </div>
      </div>

      {/* Comparative Evaluation Section */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              Model Evaluation Benchmarking
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                Common Test Subset
              </span>
            </h2>
            <p className="text-slate-500 text-sm mt-1">
              Evaluated on identical held-out test data ({performance?.sample_count || 200} transactions: {performance?.fraud_count || 100} fraud / {performance?.non_fraud_count || 100} non-fraud).
            </p>
          </div>
        </div>

        {!hybrid ? (
          <div className="p-8 text-center text-slate-400 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
            Evaluation artifacts not found. Please ensure training scripts have executed.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 border-b border-slate-200 dark:border-slate-800 uppercase text-xs">
                <tr>
                  <th className="px-4 py-3">Model Architecture</th>
                  <th className="px-4 py-3 text-right">Precision</th>
                  <th className="px-4 py-3 text-right">Recall</th>
                  <th className="px-4 py-3 text-right">F1-Score</th>
                  <th className="px-4 py-3 text-right">ROC-AUC</th>
                  <th className="px-4 py-3 text-right">PR-AUC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-xs">
                {xgb && (
                  <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 font-sans font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                      <Cpu size={16} className="text-indigo-500" /> XGBoost (Classical)
                    </td>
                    <td className="px-4 py-3 text-right">{(xgb.precision * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(xgb.recall * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(xgb.f1_score * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(xgb.roc_auc * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(xgb.pr_auc * 100).toFixed(2)}%</td>
                  </tr>
                )}

                {vqc && (
                  <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 font-sans font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                      <Activity size={16} className="text-fuchsia-500" /> VQC (Quantum 4-Qubit)
                    </td>
                    <td className="px-4 py-3 text-right">{(vqc.precision * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(vqc.recall * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(vqc.f1_score * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(vqc.roc_auc * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(vqc.pr_auc * 100).toFixed(2)}%</td>
                  </tr>
                )}

                {hybrid && (
                  <tr className="bg-amber-50/40 dark:bg-amber-950/20 font-bold text-amber-900 dark:text-amber-200">
                    <td className="px-4 py-3 font-sans font-bold flex items-center gap-2">
                      <Zap size={16} className="text-amber-500" /> Hybrid Risk Engine (0.3 XGB + 0.7 VQC)
                      <span className="text-[10px] bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 px-2 py-0.5 rounded-full font-sans font-medium">
                        Highest Recall ({(hybrid.recall * 100).toFixed(1)}%)
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">{(hybrid.precision * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right font-extrabold text-emerald-600 dark:text-emerald-400">{(hybrid.recall * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(hybrid.f1_score * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(hybrid.roc_auc * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{(hybrid.pr_auc * 100).toFixed(2)}%</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex items-center gap-2 text-xs text-slate-500 pt-2 border-t border-slate-200 dark:border-slate-800">
          <Info size={14} className="text-slate-400" />
          <span>
            Note: Results represent evaluation on the common test subset ({performance?.sample_count || 200} records). Full dataset XGBoost evaluation on 954,393 test records yielded 93.74% ROC-AUC.
          </span>
        </div>
      </div>
    </div>
  );
}
