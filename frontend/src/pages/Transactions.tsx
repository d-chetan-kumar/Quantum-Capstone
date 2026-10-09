import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { Link } from 'react-router-dom';
import { Search, Plus, CreditCard, ExternalLink, RefreshCw } from 'lucide-react';
import { formatISTDate } from '../utils/dateUtils';

export default function Transactions() {

  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const fetchTransactions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API_BASE_URL}/transactions`);
      const data = res.data;
      setTransactions(Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : []));
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

    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <CreditCard className="text-indigo-500" size={32} /> Transactions Explorer
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Browse and inspect all application payments processed by classical and quantum models.
          </p>
        </div>

        <Link
          to="/simulator"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-lg transition text-sm shadow-sm"
        >
          <Plus size={18} /> Simulate Payment
        </Link>
      </div>

      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search by Transaction ID or Sender..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
          >
            <option value="">All Transaction Types</option>
            <option value="TRANSFER">TRANSFER</option>
            <option value="CASH_OUT">CASH_OUT</option>
            <option value="PAYMENT">PAYMENT</option>
            <option value="CASH_IN">CASH_IN</option>
            <option value="DEBIT">DEBIT</option>
          </select>

          <button
            onClick={fetchTransactions}
            className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300 transition"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Content Table / States */}
        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading payment transactions...</div>
        ) : error ? (
          <div className="text-center py-12 text-slate-500 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
            <p className="font-semibold text-slate-700 dark:text-slate-300">No persistent transactions found</p>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              PostgreSQL database is currently disconnected or contains no records. Use the Payment Simulator to test real-time processing.
            </p>
          </div>
        ) : filteredTxs.length === 0 ? (
          <div className="text-center py-12 text-slate-500 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
            <p className="font-semibold text-slate-700 dark:text-slate-300">No transactions match your search</p>
            <p className="text-xs text-slate-400">Try clearing your search query or filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead className="bg-slate-50 dark:bg-slate-800/40 text-slate-500 uppercase text-[11px] border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Transaction ID</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Sender</th>
                  <th className="px-4 py-3">Receiver</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Timestamp</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-xs">
                {filteredTxs.map((tx: any) => (
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
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{tx.sender_id}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{tx.receiver_id}</td>
                    <td className="px-4 py-3 font-sans">
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold text-xs">{tx.status}</span>
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
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
