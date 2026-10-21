export type TransferStatus = 'pending' | 'connecting' | 'downloading' | 'verifying' | 'completed' | 'failed' | 'cancelled';
export type TransferDirection = 'upload' | 'download';

export interface TransferInfo {
  transfer_id: string;
  file_id: string;
  filename: string;
  source_peer_id: string;
  dest_peer_id: string;
  direction: TransferDirection;
  status: TransferStatus;
  bytes_transferred: number;
  total_bytes: number;
  progress_percent: number;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  speed_bps: number;
}

export interface DownloadRequest {
  file_id: string;
  peer_id: string;
  filename: string;
}

export interface TransferListResponse {
  transfers: TransferInfo[];
  total: number;
}

export interface CancelTransferResponse {
  transfer_id: string;
  status: string;
  message: string;
}
