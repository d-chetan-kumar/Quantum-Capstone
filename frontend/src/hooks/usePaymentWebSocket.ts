import { useState, useEffect, useRef, useCallback } from 'react';

export type ConnectionStatus = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'ERROR';

export interface PaymentEvent {
  event: string;
  transaction_id: string;
  amount: number;
  transaction_type: string;
  sender_id?: string;
  receiver_id?: string;
  classical_probability: number;
  quantum_probability: number;
  hybrid_probability: number;
  risk_level: 'SAFE' | 'REVIEW' | 'ALERT';
  status: string;
  timestamp: string;
  processing_time_ms: number;
  persisted?: boolean;
}

export interface AlertEvent {
  event: string;
  transaction_id: string;
  amount: number;
  risk_level: 'ALERT';
  hybrid_probability: number;
  alert_reason: string;
  timestamp: string;
}

import { API_BASE_URL } from '../config';

export function usePaymentWebSocket() {
  const [status, setStatus] = useState<ConnectionStatus>('CONNECTING');
  const [events, setEvents] = useState<PaymentEvent[]>([]);
  const [latestAlert, setLatestAlert] = useState<AlertEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const getWsUrl = () => {
    const apiBase = API_BASE_URL;
    const wsBase = apiBase.replace(/^http/, 'ws').replace(/\/api\/v1$/, '/ws/v1');
    return `${wsBase}/payments`;
  };

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setStatus('CONNECTING');
    const url = getWsUrl();
    console.log('[WebSocket] Connecting to:', url);

    try {
      const socket = new WebSocket(url);
      wsRef.current = socket;

      socket.onopen = () => {
        console.log('[WebSocket] Connected');
        setStatus('CONNECTED');
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'payment.processed') {
            setEvents((prev) => [payload as PaymentEvent, ...prev.slice(0, 49)]); // Keep last 50
          } else if (payload.event === 'fraud.alert') {
            setLatestAlert(payload as AlertEvent);
          }
        } catch (e) {
          console.warn('[WebSocket] Non-JSON message received:', event.data);
        }
      };

      socket.onerror = (err) => {
        console.error('[WebSocket] Error:', err);
        setStatus('ERROR');
      };

      socket.onclose = () => {
        console.log('[WebSocket] Closed');
        setStatus('DISCONNECTED');
        // Reconnect after 3 seconds
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    } catch (e) {
      console.error('[WebSocket] Exception during connection:', e);
      setStatus('ERROR');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect trigger on manual unmount
        wsRef.current.close();
      }
    };
  }, [connect]);

  const clearEvents = () => {
    setEvents([]);
    setLatestAlert(null);
  };

  return { status, events, latestAlert, clearEvents, reconnect: connect };
}
