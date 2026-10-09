import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export default function BackendStatus() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/health`);
        if (res.data.status === 'ok') {
          setBackendStatus('connected');
        } else {
          setBackendStatus('disconnected');
        }
        
        if (res.data.database === 'connected') {
            setDbStatus('connected');
        } else {
            setDbStatus('disconnected');
        }
      } catch {
        setBackendStatus('disconnected');
        setDbStatus('disconnected');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-sm flex flex-col gap-1">
      <div className="flex items-center gap-2">
          Backend: 
          {backendStatus === 'checking' && <span className="text-yellow-500">Checking...</span>}
          {backendStatus === 'connected' && <span className="text-green-500">● Connected</span>}
          {backendStatus === 'disconnected' && <span className="text-red-500">○ Disconnected</span>}
      </div>
      <div className="flex items-center gap-2">
          Database: 
          {dbStatus === 'checking' && <span className="text-yellow-500">Checking...</span>}
          {dbStatus === 'connected' && <span className="text-green-500">● Connected</span>}
          {dbStatus === 'disconnected' && <span className="text-red-500">○ Disconnected</span>}
      </div>
    </div>
  );
}
