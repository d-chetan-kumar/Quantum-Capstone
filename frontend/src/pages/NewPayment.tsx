import { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useNavigate } from 'react-router-dom';

export default function NewPayment() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    transaction_type: 'TRANSFER',
    amount: '',
    sender_id: '',
    receiver_id: '',
    location: '',
    is_simulated: true
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const s = formData.sender_id.trim();
    const r = formData.receiver_id.trim();

    if (s && r && s === r) {
      setError('Sender ID and Receiver ID cannot be identical.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/transactions/`, {
        ...formData,
        sender_id: s,
        receiver_id: r,
        amount: parseFloat(formData.amount)
      });
      navigate(`/transactions/${res.data.transaction_id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join('; '));
      } else {
        setError(detail || err.message || 'Failed to submit payment');
      }
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">New Payment</h1>
      
      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
        {error && <div className="p-3 bg-red-100 text-red-700 rounded-lg text-sm">{error}</div>}
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Type</label>
            <select 
              value={formData.transaction_type}
              onChange={e => setFormData({...formData, transaction_type: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="TRANSFER">TRANSFER</option>
              <option value="PAYMENT">PAYMENT</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Amount (₹)</label>
            <input 
              type="number" required min="1" step="0.01"
              value={formData.amount}
              onChange={e => setFormData({...formData, amount: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Sender ID</label>
            <input 
              type="text" required placeholder="••••4821"
              value={formData.sender_id}
              onChange={e => setFormData({...formData, sender_id: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Receiver ID</label>
            <input 
              type="text" required placeholder="••••9017"
              value={formData.receiver_id}
              onChange={e => setFormData({...formData, receiver_id: e.target.value})}
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Location</label>
          <input 
            type="text" placeholder="e.g. Chennai"
            value={formData.location}
            onChange={e => setFormData({...formData, location: e.target.value})}
            className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
          <button 
            type="submit" 
            disabled={submitting}
            className="w-full bg-indigo-600 text-white font-medium py-3 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
          >
            {submitting ? 'Processing...' : 'Submit Payment Request'}
          </button>
        </div>
      </form>
    </div>
  );
}
