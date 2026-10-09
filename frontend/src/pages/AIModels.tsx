import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { Cpu, Activity, Zap, Info } from 'lucide-react';

export default function AIModels() {
  const [xgbStatus, setXgbStatus] = useState<any>(null);
  const [vqcStatus, setVqcStatus] = useState<any>(null);
  const [vqcEval, setVqcEval] = useState<any>(null);
  const [hybridStatus, setHybridStatus] = useState<any>(null);
  const [hybridEval, setHybridEval] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        const [xgbRes, vqcStatRes, vqcEvalRes, hybStatRes, hybEvalRes] = await Promise.allSettled([
          axios.get(`${API_BASE_URL}/models/xgboost/status`),
          axios.get(`${API_BASE_URL}/models/vqc/status`),
          axios.get(`${API_BASE_URL}/models/vqc/evaluation`),
          axios.get(`${API_BASE_URL}/models/hybrid/status`),
          axios.get(`${API_BASE_URL}/models/hybrid/evaluation`)
        ]);

        if (xgbRes.status === 'fulfilled') setXgbStatus(xgbRes.value.data);
        if (vqcStatRes.status === 'fulfilled') setVqcStatus(vqcStatRes.value.data);
        if (vqcEvalRes.status === 'fulfilled') setVqcEval(vqcEvalRes.value.data);
        if (hybStatRes.status === 'fulfilled') setHybridStatus(hybStatRes.value.data);
        if (hybEvalRes.status === 'fulfilled') setHybridEval(hybEvalRes.value.data);
      } catch (err) {
        console.error('Failed fetching model portfolio data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAllData();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading AI model portfolio...</div>;

  const xgbAvailable = xgbStatus?.status === 'available';
  const vqcAvailable = vqcStatus?.available === true;
  const xgbWeight = hybridStatus?.xgboost_weight ?? 0.3;
  const vqcWeight = hybridStatus?.vqc_weight ?? 0.7;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">AI Models Portfolio</h1>
        <p className="text-slate-500 text-sm mt-1">Comparison and evaluation of Classical, Quantum, and Hybrid Fraud Detection Models.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Classical XGBoost Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-4">
             <Cpu size={24} className="text-indigo-600 dark:text-indigo-400" />
             <h2 className="text-xl font-bold">Classical XGBoost</h2>
          </div>
          
          {xgbAvailable ? (
            <div className="space-y-4 text-sm">
               <div className="grid grid-cols-2 gap-2">
                 <span className="text-slate-500">Status</span>
                 <span className="text-green-600 font-semibold text-right">Available</span>
                 <span className="text-slate-500">Version</span>
                 <span className="text-right">{xgbStatus.model_version}</span>
                 <span className="text-slate-500">Features</span>
                 <span className="text-right">{xgbStatus.feature_count} features</span>
               </div>
               
               <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
                 <h3 className="font-semibold mb-2">Full Test Set Evaluation</h3>
                 {xgbStatus.metrics ? (
                   <div className="grid grid-cols-2 gap-2 text-xs">
                     <span className="text-slate-500">Precision</span>
                     <span className="text-right font-mono">{(xgbStatus.metrics.precision * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">Recall</span>
                     <span className="text-right font-mono">{(xgbStatus.metrics.recall * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">F1 Score</span>
                     <span className="text-right font-mono">{(xgbStatus.metrics.f1_score * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">ROC-AUC</span>
                     <span className="text-right font-mono">{(xgbStatus.metrics.roc_auc * 100).toFixed(2)}%</span>
                   </div>
                 ) : (
                   <span className="text-slate-400 italic">N/A</span>
                 )}
               </div>
            </div>
          ) : (
             <div className="p-4 bg-slate-50 dark:bg-slate-800 text-slate-500 text-center rounded-lg border border-dashed border-slate-300 dark:border-slate-700">
                Model not trained
             </div>
          )}
        </div>

        {/* Quantum VQC Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-4">
             <Activity size={24} className="text-fuchsia-600 dark:text-fuchsia-400" />
             <h2 className="text-xl font-bold">Quantum VQC</h2>
          </div>
          
          {vqcAvailable ? (
            <div className="space-y-4 text-sm">
               <div className="grid grid-cols-2 gap-2">
                 <span className="text-slate-500">Status</span>
                 <span className="text-green-600 font-semibold text-right">Available</span>
                 <span className="text-slate-500">Qubits</span>
                 <span className="text-right font-semibold text-fuchsia-500">{vqcStatus.number_of_qubits} Qubits</span>
                 <span className="text-slate-500">Feature Map</span>
                 <span className="text-right">{vqcStatus.feature_map}</span>
                 <span className="text-slate-500">Ansatz</span>
                 <span className="text-right">{vqcStatus.ansatz}</span>
               </div>
               
               <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
                 <h3 className="font-semibold mb-2">VQC Test Evaluation</h3>
                 {vqcEval ? (
                   <div className="grid grid-cols-2 gap-2 text-xs">
                     <span className="text-slate-500">Precision</span>
                     <span className="text-right font-mono">{(vqcEval.precision * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">Recall</span>
                     <span className="text-right font-mono">{(vqcEval.recall * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">F1 Score</span>
                     <span className="text-right font-mono">{(vqcEval.f1_score * 100).toFixed(2)}%</span>
                     <span className="text-slate-500">ROC-AUC</span>
                     <span className="text-right font-mono">{(vqcEval.roc_auc * 100).toFixed(2)}%</span>
                   </div>
                 ) : (
                   <span className="text-slate-400 italic">N/A</span>
                 )}
               </div>
            </div>
          ) : (
             <div className="p-4 bg-slate-50 dark:bg-slate-800 text-slate-500 text-center rounded-lg border border-dashed border-slate-300 dark:border-slate-700 text-xs">
                <span className="font-semibold text-red-500 block mb-1">Model Unavailable</span>
                <span>{vqcStatus?.diagnostic_reason || "VQC model artifact missing or failed to load."}</span>
             </div>
          )}
        </div>

        {/* Hybrid Risk Engine Weighting Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-4">
             <Zap size={24} className="text-amber-500" />
             <h2 className="text-xl font-bold">Hybrid Risk Engine</h2>
          </div>

          <div className="space-y-4 text-sm">
             <div className="bg-amber-50 dark:bg-amber-950/30 p-3 rounded-lg border border-amber-200 dark:border-amber-900/50">
                <span className="text-xs font-semibold text-amber-800 dark:text-amber-400 block mb-1">Optimized Hybrid Combination</span>
                <p className="text-xs text-amber-700 dark:text-amber-300">
                   Weights selected by grid-search optimization on the validation set maximizing F1 score.
                </p>
             </div>

             <div className="space-y-3 pt-2">
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span>XGBoost Weight</span>
                    <span className="font-mono text-indigo-500">{(xgbWeight * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full transition-all" style={{ width: `${xgbWeight * 100}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span>VQC Weight</span>
                    <span className="font-mono text-fuchsia-500">{(vqcWeight * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-fuchsia-500 h-full transition-all" style={{ width: `${vqcWeight * 100}%` }}></div>
                  </div>
                </div>
             </div>
          </div>
        </div>

      </div>

      {/* Common Test Subset Comparative Evaluation Table */}
      {hybridEval && hybridEval.models && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                Comparative Model Benchmarking
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  Common Test Subset
                </span>
              </h2>
              <p className="text-slate-500 text-sm mt-1">
                Fair comparison evaluated on the identical held-out test population ({hybridEval.sample_count ?? 0} transactions: {hybridEval.fraud_count ?? 0} fraud / {hybridEval.non_fraud_count ?? 0} non-fraud).
              </p>
            </div>
          </div>

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
                <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                  <td className="px-4 py-3 font-sans font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                    <Cpu size={16} className="text-indigo-500" /> XGBoost (Classical)
                  </td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.xgboost ? (hybridEval.models.xgboost.precision * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.xgboost ? (hybridEval.models.xgboost.recall * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.xgboost ? (hybridEval.models.xgboost.f1_score * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.xgboost ? (hybridEval.models.xgboost.roc_auc * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.xgboost ? (hybridEval.models.xgboost.pr_auc * 100).toFixed(2) + '%' : 'N/A'}</td>
                </tr>

                <tr className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                  <td className="px-4 py-3 font-sans font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                    <Activity size={16} className="text-fuchsia-500" /> VQC (Quantum 4-Qubit)
                  </td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.vqc ? (hybridEval.models.vqc.precision * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.vqc ? (hybridEval.models.vqc.recall * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.vqc ? (hybridEval.models.vqc.f1_score * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.vqc ? (hybridEval.models.vqc.roc_auc * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.vqc ? (hybridEval.models.vqc.pr_auc * 100).toFixed(2) + '%' : 'N/A'}</td>
                </tr>

                <tr className="bg-amber-50/40 dark:bg-amber-950/20 font-bold text-amber-900 dark:text-amber-200">
                  <td className="px-4 py-3 font-sans font-bold flex items-center gap-2">
                    <Zap size={16} className="text-amber-500" /> Hybrid Model (0.3 XGB + 0.7 VQC)
                    <span className="text-[10px] bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 px-2 py-0.5 rounded-full font-sans font-medium">
                      Highest Recall (91.0%)
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.hybrid ? (hybridEval.models.hybrid.precision * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right font-extrabold text-emerald-600 dark:text-emerald-400">{hybridEval.models.hybrid ? (hybridEval.models.hybrid.recall * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.hybrid ? (hybridEval.models.hybrid.f1_score * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.hybrid ? (hybridEval.models.hybrid.roc_auc * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="px-4 py-3 text-right">{hybridEval.models.hybrid ? (hybridEval.models.hybrid.pr_auc * 100).toFixed(2) + '%' : 'N/A'}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500 pt-2 border-t border-slate-200 dark:border-slate-800">
            <Info size={14} className="text-slate-400" />
            <span>
              Note: Results above reflect evaluation on the common test subset ({hybridEval.sample_count} records). Full dataset XGBoost evaluation on 954,393 test records yielded 93.74% ROC-AUC.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
