import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: string;
  accentColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  accentColor = 'text-indigo-500'
}) => {
  return (
    <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-start justify-between">
      <div>
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
          {title}
        </span>
        <div className="text-2xl font-extrabold text-slate-900 dark:text-white font-mono">
          {value}
        </div>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        {trend && <span className="text-[11px] font-semibold text-emerald-500 mt-1 block">{trend}</span>}
      </div>

      {Icon && (
        <div className={`p-2.5 bg-slate-50 dark:bg-slate-800/80 rounded-lg ${accentColor}`}>
          <Icon size={20} />
        </div>
      )}
    </div>
  );
};
