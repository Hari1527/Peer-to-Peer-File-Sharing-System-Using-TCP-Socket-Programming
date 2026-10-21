import { ApiClient } from './apiClient';
import type { HealthResponse, TrackerStats } from '../types/events';
import type { PeerListResponse } from '../types/peer';
import type { FileListResponse, FileSearchResult, FilePeersResponse } from '../types/file';
import type { TransferListResponse } from '../types/transfer';

export class TrackerApiService {
  private client: ApiClient;

  constructor(baseUrl: string) {
    this.client = new ApiClient(baseUrl);
  }

  setBaseUrl(url: string) { this.client.setBaseUrl(url); }

  getHealth()  { return this.client.get<HealthResponse>('/api/health'); }
  getPeers(status?: string) {
    const params: Record<string, string> = {};
    if (status) params.status = status;
    return this.client.get<PeerListResponse>('/api/peers', params);
  }
  getFiles(limit = 100, offset = 0) {
    return this.client.get<FileListResponse>('/api/files', { limit: String(limit), offset: String(offset) });
  }
  searchFiles(query: string) {
    return this.client.get<FileSearchResult>('/api/files/search', { q: query });
  }
  getFilePeers(fileId: string) {
    return this.client.get<FilePeersResponse>(`/api/files/${fileId}/peers`);
  }
  getTransfers(limit = 50, offset = 0) {
    return this.client.get<TransferListResponse>('/api/transfers', { limit: String(limit), offset: String(offset) });
  }
  getStats() { return this.client.get<TrackerStats>('/api/stats'); }
}
