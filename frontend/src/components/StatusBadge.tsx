import React from 'react';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

interface StatusBadgeProps {
  status: 'online' | 'offline' | 'connected' | 'disconnected' | 'available' | 'unavailable' | 'connecting' | string;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const statusLower = status.toLowerCase();
  const displayLabel = label || status;

  if (['online', 'connected', 'available'].includes(statusLower)) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
        <CheckCircle2 size={12} /> {displayLabel}
      </span>
    );
  }

  if (['connecting'].includes(statusLower)) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
        <RefreshCw size={12} className="animate-spin" /> {displayLabel}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
      <XCircle size={12} /> {displayLabel}
    </span>
  );
};
