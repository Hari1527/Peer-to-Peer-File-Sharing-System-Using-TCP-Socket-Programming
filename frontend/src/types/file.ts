import type { PeerInfo } from './peer';

export interface SharedFileInfo {
  file_id: string;
  filename: string;
  size: number;
  checksum: string;
  peer_id: string;
  shared_at: string;
}

export interface FileListResponse {
  files: SharedFileInfo[];
  total: number;
}

export interface FileSearchResult {
  files: SharedFileInfo[];
  total: number;
  query: string;
}

export interface FilePeersResponse {
  file_id: string;
  filename: string;
  size: number;
  checksum: string;
  peers: PeerInfo[];
}

export interface ShareFilesRequest {
  directory?: string;
}

export interface ShareFilesResponse {
  files: SharedFileInfo[];
  total: number;
  message: string;
}
