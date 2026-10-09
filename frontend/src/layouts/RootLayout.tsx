import { Outlet, Link, useLocation } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import {
  Activity,
  LayoutDashboard,
  Settings as SettingsIcon,
  Cpu,
  Radio,
  Send,
  ShieldAlert,
  BarChart3,
  BookOpen,
  CreditCard,
  Sun,
  Moon,
  Scale
} from 'lucide-react';
import BackendStatus from '../components/BackendStatus';

export default function RootLayout() {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Live Payments', path: '/live', icon: Radio, highlight: true },
    { label: 'Transactions', path: '/transactions', icon: CreditCard },
    { label: 'Risk Analysis', path: '/risk-analysis', icon: Scale },
    { label: 'Alerts', path: '/alerts', icon: ShieldAlert },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
    { label: 'AI Models', path: '/models', icon: Cpu },
    { label: 'VQC Lab', path: '/vqc-lab', icon: Activity },
    { label: 'Methodology', path: '/methodology', icon: BookOpen },
    { label: 'Simulator', path: '/simulator', icon: Send },
    { label: 'Settings', path: '/settings', icon: SettingsIcon },
  ];

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans">
      <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 flex flex-col shadow-sm">
        <div className="font-bold text-xl mb-6 flex items-center gap-2.5 px-2">
          <div className="p-2 bg-indigo-600 rounded-lg text-white shadow-md">
            <Activity size={20} />
          </div>
          <div>
            <span className="bg-gradient-to-r from-indigo-600 to-fuchsia-600 bg-clip-text text-transparent font-extrabold">
              QuantumFraud
            </span>
            <span className="text-[10px] block font-mono text-slate-400 tracking-wider">AI SECURITY PLATFORM</span>
          </div>
        </div>
        
        <nav className="flex-1 space-y-1 text-sm overflow-y-auto pr-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3 py-2.5 rounded-xl font-medium transition ${
                  active
                    ? 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-semibold shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={18} className={active ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'} />
                  <span>{item.label}</span>
                </div>
                {item.highlight && (
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t pt-4 border-slate-200 dark:border-slate-800 space-y-3">
           <BackendStatus />
           <button
             onClick={toggleTheme}
             className="w-full flex items-center justify-center gap-2 text-xs font-semibold py-2 px-3 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg transition"
           >
             {theme === 'dark' ? <Sun size={14} className="text-amber-400" /> : <Moon size={14} className="text-indigo-600" />}
             <span>Theme ({theme.toUpperCase()})</span>
           </button>
        </div>
      </aside>

      <main className="flex-1 p-8 bg-slate-50 dark:bg-slate-950 h-screen overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
