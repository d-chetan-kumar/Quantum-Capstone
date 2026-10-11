const isBrowser = typeof window !== 'undefined';
const host = isBrowser ? window.location.host : 'localhost:8000';
const protocol = isBrowser && window.location.protocol === 'https:' ? 'https:' : 'http:';
const wsProtocol = isBrowser && window.location.protocol === 'https:' ? 'wss:' : 'ws:';

const isViteDev = isBrowser && window.location.port === '5173';
const isRemoteAccess = isBrowser && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

const envApi = import.meta.env.VITE_API_BASE_URL;
const envWs = import.meta.env.VITE_WS_BASE_URL;

// Determine if configured env variable points to a valid remote URL or local dev
const isUsefulEnvApi = envApi && (!isRemoteAccess || (!envApi.includes('localhost') && !envApi.includes('127.0.0.1')));
const isUsefulEnvWs = envWs && (!isRemoteAccess || (!envWs.includes('localhost') && !envWs.includes('127.0.0.1')));

export const API_BASE_URL =
  (isUsefulEnvApi ? envApi : null) ||
  (isViteDev ? 'http://localhost:8000/api/v1' : `${protocol}//${host}/api/v1`);

export const WS_BASE_URL =
  (isUsefulEnvWs ? envWs : null) ||
  (isViteDev ? 'ws://localhost:8000/ws/v1/stream' : `${wsProtocol}//${host}/ws/v1/stream`);


