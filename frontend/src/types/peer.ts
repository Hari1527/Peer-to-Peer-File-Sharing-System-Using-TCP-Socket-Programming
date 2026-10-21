export interface PeerInfo {
  peer_id: string;
  host: string;
  tcp_port: number;
  api_port: number;
  status: 'online' | 'offline';
  last_seen: string;
  file_count: number;
}

export interface PeerStatus {
  peer_id: string;
  host: string;
  tcp_port: number;
  api_port: number;
  status: string;
  shared_dir: string;
  download_dir: string;
  files_shared: number;
  active_transfers: number;
}

export interface PeerListResponse {
  peers: PeerInfo[];
  total: number;
}
