import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { Link } from 'react-router-dom';
import { Search, Plus, CreditCard, ExternalLink, RefreshCw, CheckCircle2, AlertTriangle, AlertOctagon, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatISTDate } from '../utils/dateUtils';
import { RiskBadge } from '../components/RiskBadge';

export default function Transactions() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [summary, setSummary] = useState<{ total: number; safe: number; review: number; alert: number } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 25;

  const fetchTransactions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API_BASE_URL}/transactions?limit=600`);
      const data = res.data;
      const items = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : []);
      setTransactions(items);

      if (data?.summary) {
        setSummary(data.summary);
      } else {
        const safe = items.filter((t: any) => t.risk_level === 'SAFE').length;
        const review = items.filter((t: any) => t.risk_level === 'REVIEW').length;
        const alert = items.filter((t: any) => t.risk_level === 'ALERT').length;
        setSummary({ total: items.length, safe, review, alert });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const safeTransactions = Array.isArray(transactions) ? transactions : [];
  const filteredTxs = safeTransactions.filter((tx) => {
    const matchesSearch =
      !searchTerm ||
      tx.transaction_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.sender_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.receiver_id?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType = !typeFilter || tx.transaction_type === typeFilter;
    const matchesRisk = !riskFilter || tx.risk_level === riskFilter;

    return matchesSearch && matchesType && matchesRisk;
  });

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredTxs.length / pageSize));
  const paginatedTxs = filteredTxs.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  // Compute live counts from current loaded records if summary not yet available
  const totalCount = summary?.total ?? safeTransactions.length;
  const safeCount = summary?.safe ?? safeTransactions.filter((t: any) => t.risk_level === 'SAFE').length;
  const reviewCount = summary?.review ?? safeTransactions.filter((t: any) => t.risk_level === 'REVIEW').length;
  const alertCount = summary?.alert ?? safeTransactions.filter((t: any) => t.risk_level === 'ALERT').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <CreditCard className="text-indigo-500" size={32} /> Transactions Explorer
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Browse and inspect all application payments evaluated by classical XGBoost and Quantum VQC models.
          </p>
        </div>

        <Link
          to="/simulator"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-lg transition text-sm shadow-sm"
        >
          <Plus size={18} /> Simulate Payment
        </Link>
      </div>

      {/* KPI Cards: Verified Decisions Breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-slate-500 text-xs font-semibold uppercase block">Total Transactions</span>
          <span className="text-2xl font-bold text-slate-900 dark:text-white font-mono mt-1 block">
            {totalCount}
          </span>
          <span className="text-[11px] text-slate-400 mt-0.5 block">100% Evaluated by AI</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/50 shadow-sm bg-emerald-50/20">
          <span className="text-emerald-700 dark:text-emerald-400 text-xs font-semibold uppercase flex items-center gap-1">
            <CheckCircle2 size={13} /> Safe Decisions (&lt;30%)
          </span>
          <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-1 block">
            {safeCount}
          </span>
          <span className="text-[11px] text-emerald-700/70 dark:text-emerald-500/70 mt-0.5 block">
            {totalCount > 0 ? `${((safeCount / totalCount) * 100).toFixed(1)}%` : '0%'} of all transactions
          </span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-amber-200 dark:border-amber-900/50 shadow-sm bg-amber-50/20">
          <span className="text-amber-700 dark:text-amber-400 text-xs font-semibold uppercase flex items-center gap-1">
            <AlertTriangle size={13} /> Review Required (30-70%)
          </span>
          <span className="text-2xl font-bold text-amber-600 dark:text-amber-400 font-mono mt-1 block">
            {reviewCount}
          </span>
          <span className="text-[11px] text-amber-700/70 dark:text-amber-500/70 mt-0.5 block">
            {totalCount > 0 ? `${((reviewCount / totalCount) * 100).toFixed(1)}%` : '0%'} moderate risk
          </span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-red-200 dark:border-red-900/50 shadow-sm bg-red-50/20">
          <span className="text-red-700 dark:text-red-400 text-xs font-semibold uppercase flex items-center gap-1">
            <AlertOctagon size={13} /> Fraud Alerts (&ge;70%)
          </span>
          <span className="text-2xl font-bold text-red-600 dark:text-red-400 font-mono mt-1 block">
            {alertCount}
          </span>
          <span className="text-[11px] text-red-700/70 dark:text-red-500/70 mt-0.5 block">
            {totalCount > 0 ? `${((alertCount / totalCount) * 100).toFixed(1)}%` : '0%'} high-risk flagged
          </span>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search by Transaction ID, Sender, or Receiver..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
          >
            <option value="">All Payment Types</option>
            <option value="TRANSFER">TRANSFER</option>
            <option value="CASH_OUT">CASH_OUT</option>
            <option value="PAYMENT">PAYMENT</option>
            <option value="CASH_IN">CASH_IN</option>
            <option value="DEBIT">DEBIT</option>
          </select>

          <select
            value={riskFilter}
            onChange={(e) => {
              setRiskFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
          >
            <option value="">All AI Decisions</option>
            <option value="SAFE">SAFE (&lt;30%)</option>
            <option value="REVIEW">REVIEW (30-70%)</option>
            <option value="ALERT">ALERT / FRAUD (&ge;70%)</option>
          </select>

          <button
            onClick={fetchTransactions}
            className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300 transition"
            title="Refresh transactions"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Content Table / States */}
        {loading ? (
          <div className="text-center py-12 text-slate-500">
            <RefreshCw className="animate-spin mx-auto text-indigo-500 mb-2" size={24} />
            Loading payment transactions...
          </div>
        ) : error ? (
          <div className="text-center py-12 text-slate-500 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
            <p className="font-semibold text-slate-700 dark:text-slate-300">Could not retrieve transactions</p>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">{error}</p>
          </div>
        ) : filteredTxs.length === 0 ? (
          <div className="text-center py-12 text-slate-500 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
            <p className="font-semibold text-slate-700 dark:text-slate-300">No transactions match your search or filter</p>
            <p className="text-xs text-slate-400">Try adjusting your search query, payment type, or risk decision filter.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-800/40 text-slate-500 uppercase text-[11px] border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Transaction ID</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Sender / Receiver</th>
                    <th className="px-4 py-3">AI Risk Decision</th>
                    <th className="px-4 py-3 text-right">Timestamp</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-xs">
                  {paginatedTxs.map((tx: any) => {
                    const probPct = tx.hybrid_probability !== null && tx.hybrid_probability !== undefined
                      ? (tx.hybrid_probability * 100).toFixed(1)
                      : null;

                    return (
                      <tr key={tx.transaction_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                        <td className="px-4 py-3 text-indigo-600 dark:text-indigo-400 font-semibold">
                          <Link to={`/transactions/${tx.transaction_id}`} className="hover:underline inline-flex items-center gap-1 font-mono">
                            {tx.transaction_id.substring(0, 14)}... <ExternalLink size={10} />
                          </Link>
                        </td>
                        <td className="px-4 py-3 font-sans font-medium">
                          <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs">{tx.transaction_type}</span>
                        </td>
                        <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">₹{tx.amount.toLocaleString()}</td>
                        <td className="px-4 py-3 font-sans text-xs">
                          <div className="text-slate-800 dark:text-slate-200 font-mono">{tx.sender_id}</div>
                          <div className="text-slate-400 text-[11px] font-mono">→ {tx.receiver_id}</div>
                        </td>
                        <td className="px-4 py-3 font-sans">
                          <div className="flex items-center gap-2">
                            <RiskBadge level={tx.risk_level || 'SAFE'} size="sm" />
                            {probPct && (
                              <span className="font-mono text-[11px] text-slate-500">
                                {probPct}%
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right text-slate-500 font-sans text-[11px]">
                          {formatISTDate(tx.timestamp || tx.created_at)}
                        </td>
                        <td className="px-4 py-3 text-right font-sans">
                          <Link
                            to={`/transactions/${tx.transaction_id}`}
                            className="text-indigo-600 dark:text-indigo-400 hover:underline text-xs inline-flex items-center gap-1 font-semibold"
                          >
                            Inspect <ExternalLink size={12} />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 text-xs text-slate-500 font-sans border-t border-slate-100 dark:border-slate-800">
              <div>
                Showing <span className="font-bold text-slate-800 dark:text-slate-200">{((currentPage - 1) * pageSize) + 1}</span> to{' '}
                <span className="font-bold text-slate-800 dark:text-slate-200">{Math.min(currentPage * pageSize, filteredTxs.length)}</span> of{' '}
                <span className="font-bold text-slate-800 dark:text-slate-200">{filteredTxs.length}</span> filtered transactions
                {filteredTxs.length !== totalCount && ` (from ${totalCount} total)`}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium transition"
                >
                  <ChevronLeft size={14} /> Previous
                </button>
                <span className="px-2 font-mono">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium transition"
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
