import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react';

interface RiskBadgeProps {
  level: 'SAFE' | 'REVIEW' | 'ALERT' | string;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, size = 'md' }) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3.5 py-1.5 text-sm',
  };

  const iconSizes = {
    sm: 12,
    md: 14,
    lg: 16,
  };

  switch (level) {
    case 'SAFE':
      return (
        <span className={`inline-flex items-center gap-1.5 font-bold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 ${sizeClasses[size]}`}>
          <CheckCircle2 size={iconSizes[size]} /> SAFE
        </span>
      );
    case 'REVIEW':
      return (
        <span className={`inline-flex items-center gap-1.5 font-bold rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800 ${sizeClasses[size]}`}>
          <AlertTriangle size={iconSizes[size]} /> REVIEW
        </span>
      );
    case 'ALERT':
      return (
        <span className={`inline-flex items-center gap-1.5 font-bold rounded-full bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border border-red-200 dark:border-red-800 animate-pulse ${sizeClasses[size]}`}>
          <AlertOctagon size={iconSizes[size]} /> ALERT
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center font-medium rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 ${sizeClasses[size]}`}>
          {level}
        </span>
      );
  }
};
