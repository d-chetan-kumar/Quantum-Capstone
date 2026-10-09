import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { Cpu, Server, Activity, ArrowRight, CheckCircle2, XCircle, Maximize2, ZoomIn, ExternalLink } from 'lucide-react';

export default function VQCLab() {
  const [status, setStatus] = useState<any>(null);
  const [evaluation, setEvaluation] = useState<any>(null);
  const [circuitViewMode, setCircuitViewMode] = useState<'interactive' | 'rendered'>('interactive');
  const [imageZoomMode, setImageZoomMode] = useState<'fit' | 'full'>('fit');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statRes, evalRes] = await Promise.allSettled([
          axios.get(`${API_BASE_URL}/models/vqc/status`),
          axios.get(`${API_BASE_URL}/models/vqc/evaluation`)
        ]);

        if (statRes.status === 'fulfilled') setStatus(statRes.value.data);
        if (evalRes.status === 'fulfilled') setEvaluation(evalRes.value.data);
      } catch (e) {
        console.error("Error fetching VQC data", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="p-8 text-center">Loading Quantum Data...</div>;

  const isAvailable = status?.available;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Cpu size={28} className="text-fuchsia-500" />
        <h1 className="text-3xl font-bold">Variational Quantum Classifier (VQC) Lab</h1>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Model Status */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Server size={20} className="text-indigo-500" />
              Quantum Model Status
            </h2>
            {isAvailable ? <CheckCircle2 className="text-green-500" /> : <XCircle className="text-red-500" />}
          </div>
          
          {isAvailable ? (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-slate-500 block">VQC Status</span><span className="text-green-600 font-medium">Available</span></div>
              <div><span className="text-slate-500 block">Model Version</span><span>{status.model_version}</span></div>
              <div><span className="text-slate-500 block">Qubit Count</span><span>{status.number_of_qubits}</span></div>
              <div><span className="text-slate-500 block">Feature Count</span><span>{status.quantum_features?.length || 4}</span></div>
              <div><span className="text-slate-500 block">Training Status</span><span className="text-green-600">Completed</span></div>
              <div><span className="text-slate-500 block">Trained At</span><span>{new Date(status.training_timestamp * 1000).toLocaleString()}</span></div>
            </div>
          ) : (
            <div className="text-slate-500 text-sm space-y-1">
              <span className="font-semibold text-red-500 block">VQC Unavailable</span>
              <p>{status?.diagnostic_reason || "VQC model artifact unavailable or failed to load."}</p>
            </div>
          )}
        </div>

        {/* Evaluation Metrics */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <h2 className="text-xl font-semibold flex items-center gap-2 mb-4">
            <Activity size={20} className="text-emerald-500" />
            Evaluation
          </h2>
          
          {evaluation ? (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg text-center">
                <span className="text-slate-500 block mb-1">Precision</span>
                <span className="text-xl font-bold">{(evaluation.precision * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg text-center">
                <span className="text-slate-500 block mb-1">Recall</span>
                <span className="text-xl font-bold">{(evaluation.recall * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg text-center">
                <span className="text-slate-500 block mb-1">F1 Score</span>
                <span className="text-xl font-bold">{(evaluation.f1_score * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg text-center">
                <span className="text-slate-500 block mb-1">ROC-AUC</span>
                <span className="text-xl font-bold">{(evaluation.roc_auc * 100).toFixed(1)}%</span>
              </div>
            </div>
          ) : (
            <div className="text-slate-500 text-sm">Evaluation not available.</div>
          )}
        </div>
        
        {/* VQC Configuration */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <h2 className="text-xl font-semibold mb-4">VQC Configuration</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
             <div><span className="text-slate-500 block">Qubits</span><span>4</span></div>
             <div><span className="text-slate-500 block">Feature Map</span><span>ZZFeatureMap</span></div>
             <div><span className="text-slate-500 block">Feature Map Repetitions</span><span>1</span></div>
             <div><span className="text-slate-500 block">Ansatz</span><span>RealAmplitudes</span></div>
             <div><span className="text-slate-500 block">Ansatz Repetitions</span><span>2</span></div>
             <div><span className="text-slate-500 block">Entanglement</span><span>Linear</span></div>
             <div><span className="text-slate-500 block">Optimizer</span><span>COBYLA</span></div>
          </div>
        </div>

        {/* Quantum Pipeline & Features */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
          <h2 className="text-xl font-semibold mb-4">Quantum Pipeline</h2>
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-600 dark:text-slate-400 mb-6 bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
            <span>Features</span><ArrowRight size={14} />
            <span>Scaling</span><ArrowRight size={14} />
            <span className="text-fuchsia-600 dark:text-fuchsia-400">ZZFeatureMap</span><ArrowRight size={14} />
            <span className="text-indigo-600 dark:text-indigo-400">RealAmplitudes</span><ArrowRight size={14} />
            <span>Measurement</span><ArrowRight size={14} />
            <span>Probability</span>
          </div>

          <h3 className="text-md font-semibold mb-2">Quantum Features</h3>
          <ul className="text-sm space-y-2">
            <li><span className="font-mono text-slate-700 dark:text-slate-300">transaction_type</span> - Encoded transaction category</li>
            <li><span className="font-mono text-slate-700 dark:text-slate-300">hour_of_day</span> - Extracted hour from timestamp or step</li>
            <li><span className="font-mono text-slate-700 dark:text-slate-300">day_of_week</span> - Extracted day to capture temporal patterns</li>
            <li><span className="font-mono text-slate-700 dark:text-slate-300">log_amount</span> - Natural log of transaction amount</li>
          </ul>
        </div>
      </div>

      {/* Quantum Circuit Representation */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Cpu size={22} className="text-fuchsia-500" />
              Quantum Circuit Architecture Representation
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              4-Qubit Variational Quantum Classifier combining ZZFeatureMap encoding and 2-repetition RealAmplitudes ansatz.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${isAvailable ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800' : 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800'}`}>
              {isAvailable ? 'Trained VQC Model Circuit' : 'Configured Architecture Diagram'}
            </span>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex justify-between items-center text-xs">
          <div className="inline-flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setCircuitViewMode('interactive')}
              className={`px-3 py-1.5 font-medium rounded-md transition ${circuitViewMode === 'interactive' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
            >
              Interactive Gate-Level Diagram
            </button>
            <button
              onClick={() => setCircuitViewMode('rendered')}
              className={`px-3 py-1.5 font-medium rounded-md transition ${circuitViewMode === 'rendered' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
            >
              Qiskit High-Res Matplotlib Image
            </button>
          </div>

          <span className="text-slate-400 font-mono text-[11px]">
            4 Qubits | 12 Parameters | Linear Entanglement
          </span>
        </div>

        {/* View Content */}
        {circuitViewMode === 'interactive' ? (
          <div className="overflow-x-auto bg-slate-950 text-slate-100 p-6 rounded-xl border border-slate-800 space-y-6">
            
            {/* Stage Headers */}
            <div className="min-w-[860px] grid grid-cols-12 gap-2 text-center text-xs font-bold uppercase tracking-wider pb-3 border-b border-slate-800/80">
              <div className="col-span-2 text-left text-slate-400 font-mono">Qubit / Feature</div>
              <div className="col-span-4 bg-fuchsia-950/50 border border-fuchsia-800/40 text-fuchsia-400 py-1 rounded">
                Stage 1: ZZFeatureMap (x₀ .. x₃)
              </div>
              <div className="col-span-5 bg-indigo-950/50 border border-indigo-800/40 text-indigo-400 py-1 rounded">
                Stage 2: RealAmplitudes (θ₀ .. θ₁₁)
              </div>
              <div className="col-span-1 bg-emerald-950/50 border border-emerald-800/40 text-emerald-400 py-1 rounded">
                Stage 3
              </div>
            </div>

            {/* Qubit Wires */}
            <div className="min-w-[860px] space-y-6 pt-2 font-mono">
              {[
                { label: 'q0', feature: 'transaction_type', var: 'x₀', angles: ['θ₀', 'θ₄', 'θ₈'], cxPair: [0, 1] },
                { label: 'q1', feature: 'hour_of_day', var: 'x₁', angles: ['θ₁', 'θ₅', 'θ₉'], cxPair: [1, 2] },
                { label: 'q2', feature: 'day_of_week', var: 'x₂', angles: ['θ₂', 'θ₆', 'θ₁₀'], cxPair: [2, 3] },
                { label: 'q3', feature: 'log_amount', var: 'x₃', angles: ['θ₃', 'θ₇', 'θ₁₁'], cxPair: null }
              ].map((q, idx) => (
                <div key={q.label} className="relative flex items-center h-12">
                  {/* Background Qubit Wire */}
                  <div className="absolute left-36 right-10 h-0.5 bg-slate-700/80 z-0"></div>

                  {/* Left Feature Input Label */}
                  <div className="w-36 flex flex-col justify-center text-xs space-y-0.5 pr-3 z-10">
                    <span className="font-bold text-fuchsia-400">{q.label} | {q.var}</span>
                    <span className="text-[10px] text-slate-400 font-sans truncate">{q.feature}</span>
                  </div>

                  {/* Gate Wire Content */}
                  <div className="flex-1 flex items-center justify-between z-10 pl-2 pr-4">
                    {/* Stage 1: Feature Encoding */}
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 rounded bg-fuchsia-900/80 border border-fuchsia-400 text-fuchsia-200 font-bold text-xs flex items-center justify-center shadow">
                        H
                      </span>
                      <span className="px-2 py-1 rounded bg-fuchsia-950 border border-fuchsia-500/60 text-fuchsia-300 font-bold text-[11px] flex items-center gap-1 shadow">
                        Rz({q.var})
                      </span>
                      {/* ZZ Coupling Pair Indicator */}
                      <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-fuchsia-800 text-fuchsia-400 text-[10px]">
                        ZZ({q.var})
                      </span>
                    </div>

                    <div className="w-px h-10 bg-slate-800"></div>

                    {/* Stage 2: Variational Ansatz (Reps 0, 1, 2) */}
                    <div className="flex items-center gap-3">
                      {/* Layer 0 Rotation */}
                      <span className="px-2 py-1 rounded bg-indigo-900/90 border border-indigo-400 text-indigo-200 font-bold text-[11px] shadow">
                        Ry({q.angles[0]})
                      </span>

                      {/* Entanglement CX */}
                      {idx < 3 ? (
                        <div className="flex flex-col items-center justify-center">
                          <span className="w-3 h-3 rounded-full bg-amber-400 ring-2 ring-amber-500/50"></span>
                          <span className="text-[9px] text-amber-400 font-bold">CX</span>
                        </div>
                      ) : (
                        <span className="w-3 h-3 rounded-full bg-slate-700"></span>
                      )}

                      {/* Layer 1 Rotation */}
                      <span className="px-2 py-1 rounded bg-indigo-900/90 border border-indigo-400 text-indigo-200 font-bold text-[11px] shadow">
                        Ry({q.angles[1]})
                      </span>

                      {/* Entanglement CX */}
                      {idx < 3 ? (
                        <div className="flex flex-col items-center justify-center">
                          <span className="w-3 h-3 rounded-full bg-amber-400 ring-2 ring-amber-500/50"></span>
                          <span className="text-[9px] text-amber-400 font-bold">CX</span>
                        </div>
                      ) : (
                        <span className="w-3 h-3 rounded-full bg-slate-700"></span>
                      )}

                      {/* Layer 2 Final Rotation */}
                      <span className="px-2 py-1 rounded bg-indigo-900/90 border border-indigo-400 text-indigo-200 font-bold text-[11px] shadow">
                        Ry({q.angles[2]})
                      </span>
                    </div>

                    <div className="w-px h-10 bg-slate-800"></div>

                    {/* Stage 3: Measurement */}
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 rounded bg-emerald-900/90 border border-emerald-400 text-emerald-200 font-bold text-xs flex items-center justify-center shadow">
                        M
                      </span>
                    </div>
                  </div>

                  {/* Right Output Arrow */}
                  <div className="w-12 text-right z-10 text-xs font-bold text-emerald-400">
                    P({q.label})
                  </div>
                </div>
              ))}
            </div>

          </div>
        ) : (
          <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 text-center space-y-4">
            {/* Image Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center gap-2 text-slate-300 font-medium">
                <span className="w-2 h-2 rounded-full bg-fuchsia-500 animate-pulse"></span>
                Qiskit High-Res Circuit Render
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setImageZoomMode('fit')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center gap-1.5 ${
                    imageZoomMode === 'fit'
                      ? 'bg-fuchsia-600 text-white shadow-sm'
                      : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                  }`}
                >
                  <Maximize2 size={13} />
                  Fit to View
                </button>
                <button
                  type="button"
                  onClick={() => setImageZoomMode('full')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center gap-1.5 ${
                    imageZoomMode === 'full'
                      ? 'bg-fuchsia-600 text-white shadow-sm'
                      : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                  }`}
                >
                  <ZoomIn size={13} />
                  Full Size / Zoom
                </button>
                <a
                  href={`${API_BASE_URL}/models/vqc/circuit/image`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-md text-xs font-medium bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition flex items-center gap-1.5"
                  title="Open circuit image in new tab"
                >
                  <ExternalLink size={13} />
                  Open Image
                </a>
              </div>
            </div>

            {/* Circuit Image Container */}
            <div
              className={`w-full rounded-lg bg-slate-900/60 p-4 border border-slate-800 flex items-center justify-center transition-all ${
                imageZoomMode === 'fit'
                  ? 'max-h-[550px] overflow-hidden'
                  : 'max-h-[650px] overflow-auto'
              }`}
            >
              <img
                src={`${API_BASE_URL}/models/vqc/circuit/image`}
                alt="Qiskit Rendered VQC Quantum Circuit"
                className={`rounded shadow-md border border-slate-800/80 transition-all ${
                  imageZoomMode === 'fit'
                    ? 'w-full max-w-full h-auto object-contain max-h-[500px]'
                    : 'max-w-none w-auto h-auto'
                }`}
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Rendered directly from backend Qiskit QuantumCircuit using MatplotlibDrawer.
            </p>
          </div>
        )}

        {/* Legend Panel */}
        <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
          <span className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block text-[11px]">
            Quantum Circuit Element Legend
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <div className="flex items-center gap-2 p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
              <span className="w-3 h-3 rounded bg-fuchsia-600"></span>
              <div>
                <span className="font-bold block text-slate-800 dark:text-slate-200">Feature Encoding</span>
                <span className="text-[10px] text-slate-500">ZZFeatureMap (H, Rz(xᵢ))</span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
              <span className="w-3 h-3 rounded bg-indigo-600"></span>
              <div>
                <span className="font-bold block text-slate-800 dark:text-slate-200">Trainable Gates</span>
                <span className="text-[10px] text-slate-500">RealAmplitudes Ry(θⱼ)</span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
              <span className="w-3 h-3 rounded-full bg-amber-500"></span>
              <div>
                <span className="font-bold block text-slate-800 dark:text-slate-200">Linear Entanglement</span>
                <span className="text-[10px] text-slate-500">CNOT / CX(qₖ, qₖ₊₁)</span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
              <span className="w-3 h-3 rounded bg-emerald-600"></span>
              <div>
                <span className="font-bold block text-slate-800 dark:text-slate-200">Measurement</span>
                <span className="text-[10px] text-slate-500">Computational Basis M</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
