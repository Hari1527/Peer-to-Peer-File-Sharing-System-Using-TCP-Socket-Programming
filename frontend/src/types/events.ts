export type WebSocketEventType =
  | 'peer_registered' | 'peer_offline' | 'peer_heartbeat'
  | 'file_shared'
  | 'transfer_started' | 'transfer_progress' | 'transfer_completed' | 'transfer_failed';

export interface WebSocketEvent {
  type: WebSocketEventType;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface TrackerStats {
  peers_online: number;
  total_files: number;
  total_transfers: number;
  bytes_transferred: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export interface ActivityLogEntry {
  id: string;
  timestamp: string;
  type: WebSocketEventType;
  category: 'peer' | 'file' | 'transfer' | 'system';
  severity: 'info' | 'success' | 'warning' | 'error';
  peer_id?: string;
  message: string;
  data?: Record<string, unknown>;
}

export interface AppNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: string;
}
