import os
import textwrap

BASE_DIR = r"c:\Users\HP\OneDrive\Desktop\QUANTUM FRAUD DETECTION\frontend"

def write_file(path, content):
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

dirs = [
    "src/components",
    "src/pages",
    "src/layouts",
    "src/hooks",
    "src/services",
    "src/types",
    "src/lib",
]
for d in dirs:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

write_file("tailwind.config.js", """
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
      }
    },
  },
  plugins: [],
}
""")

write_file("postcss.config.js", """
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""")

write_file("src/index.css", """
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #ffffff;
  --foreground: #0f172a;
}

.dark {
  --background: #0f172a;
  --foreground: #f8fafc;
}

body {
  background-color: var(--background);
  color: var(--foreground);
}
""")

write_file("src/App.tsx", """
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import Dashboard from './pages/Dashboard';
import LivePayments from './pages/LivePayments';
import Settings from './pages/Settings';
import EmptyStatePage from './pages/EmptyStatePage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<RootLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="live" element={<LivePayments />} />
          <Route path="transactions" element={<EmptyStatePage title="Transactions" />} />
          <Route path="alerts" element={<EmptyStatePage title="Alerts" />} />
          <Route path="analytics" element={<EmptyStatePage title="Analytics" />} />
          <Route path="models" element={<EmptyStatePage title="AI Models" />} />
          <Route path="vqc-lab" element={<EmptyStatePage title="VQC Lab" />} />
          <Route path="methodology" element={<EmptyStatePage title="Methodology" />} />
          <Route path="simulator" element={<EmptyStatePage title="Simulator" />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
""")

write_file("src/main.tsx", """
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { ThemeProvider } from './hooks/useTheme.tsx'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
)
""")

write_file("src/hooks/useTheme.tsx", """
import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => (prev === 'light' ? 'dark' : 'light'));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) throw new Error('useTheme must be used within a ThemeProvider');
  return context;
};
""")

write_file("src/layouts/RootLayout.tsx", """
import { Outlet, Link } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { Activity, LayoutDashboard, Settings as SettingsIcon } from 'lucide-react';
import BackendStatus from '../components/BackendStatus';

export default function RootLayout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-200 dark:border-slate-800 p-4 flex flex-col">
        <div className="font-bold text-xl mb-8 flex items-center gap-2">
          <Activity className="text-indigo-600" />
          QuantumFraud
        </div>
        
        <nav className="flex-1 space-y-2">
          <Link to="/" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
            <LayoutDashboard size={18} /> Dashboard
          </Link>
          <Link to="/live" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
            <Activity size={18} /> Live Payments
          </Link>
          <Link to="/transactions" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
             Transactions
          </Link>
          <Link to="/vqc-lab" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
             VQC Lab
          </Link>
          <Link to="/settings" className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
            <SettingsIcon size={18} /> Settings
          </Link>
        </nav>

        <div className="mt-auto border-t pt-4 border-slate-200 dark:border-slate-800">
           <BackendStatus />
           <button onClick={toggleTheme} className="mt-4 text-sm px-4 py-2 bg-indigo-600 text-white rounded w-full">
             Toggle Theme ({theme})
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 bg-slate-50 dark:bg-[#0f172a]">
        <Outlet />
      </main>
    </div>
  );
}
""")

write_file("src/components/BackendStatus.tsx", """
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function BackendStatus() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await axios.get(import.meta.env.VITE_API_BASE_URL + '/health');
        if (res.data.status === 'ok') {
          setStatus('connected');
        } else {
          setStatus('disconnected');
        }
      } catch {
        setStatus('disconnected');
      }
    };
    checkHealth();
  }, []);

  return (
    <div className="text-sm flex items-center gap-2">
      Backend: 
      {status === 'checking' && <span className="text-yellow-500">Checking...</span>}
      {status === 'connected' && <span className="text-green-500">● Connected</span>}
      {status === 'disconnected' && <span className="text-red-500">○ Disconnected</span>}
    </div>
  );
}
""")

write_file("src/pages/Dashboard.tsx", """
export default function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
      <div className="p-8 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg text-center text-slate-500">
        <p>Dashboard functionality will be implemented in a future phase.</p>
        <p className="mt-2 text-sm">Real metrics and charts will appear here.</p>
      </div>
    </div>
  );
}
""")

write_file("src/pages/LivePayments.tsx", """
import { useEffect, useState } from 'react';

export default function LivePayments() {
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connected'>('disconnected');

  useEffect(() => {
    const ws = new WebSocket(import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws/v1/stream');
    
    ws.onopen = () => setWsStatus('connected');
    ws.onclose = () => setWsStatus('disconnected');

    return () => ws.close();
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Live Payments Simulator</h1>
      <div className="mb-4 text-sm">
        WebSocket Status: {wsStatus === 'connected' ? <span className="text-green-500">Connected</span> : <span className="text-red-500">Disconnected</span>}
      </div>
      <div className="p-8 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg text-center text-slate-500">
        <p>Live simulator stream will be implemented in a future phase.</p>
        <p className="mt-2 text-sm">Transactions will appear here in real time.</p>
      </div>
    </div>
  );
}
""")

write_file("src/pages/EmptyStatePage.tsx", """
export default function EmptyStatePage({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">{title}</h1>
      <div className="p-8 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg text-center text-slate-500">
        <p>{title} functionality will be implemented in a future phase.</p>
      </div>
    </div>
  );
}
""")

write_file("src/pages/Settings.tsx", """
export default function Settings() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Settings</h1>
      <div className="p-8 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg text-center text-slate-500">
        <p>Application settings will be configured here.</p>
      </div>
    </div>
  );
}
""")

print("Frontend setup complete.")
