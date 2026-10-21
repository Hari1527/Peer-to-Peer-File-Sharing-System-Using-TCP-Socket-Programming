export const DEFAULT_TRACKER_URL = import.meta.env.VITE_TRACKER_URL || 'http://localhost:8000';
export const DEFAULT_PEER_URL = import.meta.env.VITE_PEER_URL || 'http://localhost:8001';
export const DEFAULT_TRACKER_WS_URL = import.meta.env.VITE_TRACKER_WS_URL || 'ws://localhost:8000/ws/events';
export const DEFAULT_PEER_WS_URL = import.meta.env.VITE_PEER_WS_URL || 'ws://localhost:8001/ws/events';

export const REFRESH_INTERVAL = 10_000;
export const ACTIVE_REFRESH_INTERVAL = 3_000;
export const WS_RECONNECT_DELAY = 3_000;
export const WS_MAX_RECONNECT_DELAY = 30_000;
export const MAX_ACTIVITY_LOGS = 200;

export const STORAGE_KEYS = {
  TRACKER_URL: 'p2p_tracker_url',
  PEER_URL: 'p2p_peer_url',
} as const;
