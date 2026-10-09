import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import Dashboard from './pages/Dashboard';
import LivePayments from './pages/LivePayments';
import Settings from './pages/Settings';
import Transactions from './pages/Transactions';
import NewPayment from './pages/NewPayment';
import TransactionDetail from './pages/TransactionDetail';
import AIModels from './pages/AIModels';
import VQCLab from './pages/VQCLab';
import Alerts from './pages/Alerts';
import Simulator from './pages/Simulator';
import Analytics from './pages/Analytics';
import Methodology from './pages/Methodology';
import RiskAnalysis from './pages/RiskAnalysis';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<RootLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="live" element={<LivePayments />} />
          <Route path="live-payments" element={<LivePayments />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="transactions/new" element={<NewPayment />} />
          <Route path="transactions/:id" element={<TransactionDetail />} />
          <Route path="risk-analysis" element={<RiskAnalysis />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="models" element={<AIModels />} />
          <Route path="vqc-lab" element={<VQCLab />} />
          <Route path="methodology" element={<Methodology />} />
          <Route path="simulator" element={<Simulator />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
