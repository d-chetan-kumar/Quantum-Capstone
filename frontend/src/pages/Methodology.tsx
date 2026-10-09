import { useState } from 'react';
import { Database, Cpu, Activity, Zap, Radio, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function Methodology() {
  const [activeStage, setActiveStage] = useState<number>(0);

  const stages = [
    {
      id: 0,
      title: '1. PaySim Dataset & Preprocessing',
      icon: Database,
      tag: 'Data Pipeline',
      color: 'border-blue-500 text-blue-500',
      summary: '6,362,620 financial transaction records from the synthetic PaySim benchmark dataset.',
      details: [
        'PaySim dataset contains 6.36M rows with 11 standard columns (amount, type, step, balance columns).',
        'Target column isFraud (8,213 fraud instances, 0.1291% fraud ratio).',
        'Data split chronologically into 70% Train (4.45M), 15% Val (954K), 15% Test (954K).',
        'Excluded data leakage columns: isFlaggedFraud, nameOrig, nameDest, oldbalanceOrg, newbalanceOrig.'
      ]
    },
    {
      id: 1,
      title: '2. Classical XGBoost Classification',
      icon: Cpu,
      tag: 'Classical ML',
      color: 'border-indigo-500 text-indigo-500',
      summary: 'Gradient boosted decision tree model trained on 8 real-time compatible features.',
      details: [
        'Extracted features: log_amount, type_CASH_IN, type_CASH_OUT, type_DEBIT, type_PAYMENT, type_TRANSFER, hour_of_day, day_of_week.',
        'Calculated scale_pos_weight (1221.57) strictly from Train split to address class imbalance.',
        'Hyperparameters: n_estimators=100, max_depth=6, learning_rate=0.1, subsample=0.8.',
        'Achieved 93.74% ROC-AUC on the full 954,393 test set.'
      ]
    },
    {
      id: 2,
      title: '3. Quantum Variational Classifier (VQC)',
      icon: Activity,
      tag: 'Quantum AI',
      color: 'border-fuchsia-500 text-fuchsia-500',
      summary: '4-qubit Quantum Machine Learning algorithm built using Qiskit 1.3.1.',
      details: [
        '4 Quantum Features: transaction_type, hour_of_day, day_of_week, log_amount.',
        'Scaled features to [0, pi] using MinMaxScaler.',
        'Quantum Feature Map: ZZFeatureMap (feature_dimension=4, reps=1).',
        'Variational Ansatz: RealAmplitudes (num_qubits=4, entanglement=linear, reps=2).',
        'Optimizer: COBYLA (maxiter=60) running on Qiskit Statevector simulator.'
      ]
    },
    {
      id: 3,
      title: '4. Hybrid Risk Engine',
      icon: Zap,
      tag: 'Risk Fusion',
      color: 'border-amber-500 text-amber-500',
      summary: 'Optimal weighted probability fusion model: p_hybrid = 0.30 * p_xgb + 0.70 * p_vqc.',
      details: [
        'Grid-search optimization performed on Common Validation Subset maximizing F1-score.',
        'Optimal weights selected: 30% XGBoost + 70% VQC.',
        'Business Decision Thresholds: SAFE (<0.30), REVIEW (0.30–<0.70), ALERT (>=0.70).',
        'Evaluated on Common Test Subset (200 records) yielding highest recall (91.00%).'
      ]
    },
    {
      id: 4,
      title: '5. Real-Time Payment Streaming',
      icon: Radio,
      tag: 'WebSockets',
      color: 'border-emerald-500 text-emerald-500',
      summary: 'FastAPI WebSocket event architecture & Payment Gateway Simulator API.',
      details: [
        'Endpoint WS /ws/v1/payments streams real-time payment.processed events.',
        'Simulator API POST /api/v1/simulator/payment executes end-to-end model pipeline.',
        'Live Payments monitor updates instantaneously via WebSocket events without polling.',
        'ALERT decision triggers instant fraud.alert event broadcast.'
      ]
    },
    {
      id: 5,
      title: '6. Persistence & Audit Layer',
      icon: ShieldCheck,
      tag: 'Storage & Alerts',
      color: 'border-cyan-500 text-cyan-500',
      summary: 'PostgreSQL database models for transactions, predictions, and alerts.',
      details: [
        'Stores Transaction, ModelPrediction, and FraudAlert records.',
        'Provides graceful fallback mode when PostgreSQL database is offline.',
        'Alerts page allows security analysts to inspect and resolve active fraud alerts.'
      ]
    }
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold">Research & Architectural Methodology</h1>
        <p className="text-slate-500 text-sm mt-1">
          End-to-end pipeline design of the Quantum-Assisted Real-Time Payment Fraud Detection System.
        </p>
      </div>

      {/* Stage Selector Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {stages.map((stage) => {
          const Icon = stage.icon;
          const isSelected = activeStage === stage.id;
          return (
            <div
              key={stage.id}
              onClick={() => setActiveStage(stage.id)}
              className={`cursor-pointer p-5 rounded-xl border transition shadow-sm ${
                isSelected
                  ? `bg-white dark:bg-slate-900 border-2 ${stage.color}`
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                  {stage.tag}
                </span>
                <Icon size={20} className={isSelected ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'} />
              </div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">{stage.title}</h3>
              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{stage.summary}</p>
            </div>
          );
        })}
      </div>

      {/* Selected Stage Detail Panel */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
          {(() => {
            const CurrentIcon = stages[activeStage].icon;
            return <CurrentIcon size={24} className="text-indigo-600 dark:text-indigo-400" />;
          })()}
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {stages[activeStage].title}
            </h2>
            <p className="text-xs text-slate-500">{stages[activeStage].summary}</p>
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Key Technical Specifications</h4>
          <ul className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
            {stages[activeStage].details.map((detail, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs">
                <CheckCircle2 size={16} className="text-indigo-500 shrink-0 mt-0.5" />
                <span>{detail}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
