import { ApiClient } from './apiClient';
import type { PeerStatus } from '../types/peer';
import type { FileListResponse, ShareFilesResponse } from '../types/file';
import type { TransferInfo, TransferListResponse, DownloadRequest, CancelTransferResponse } from '../types/transfer';

export class PeerApiService {
  private client: ApiClient;

  constructor(baseUrl: string) {
    this.client = new ApiClient(baseUrl);
  }

  setBaseUrl(url: string) { this.client.setBaseUrl(url); }

  getStatus()    { return this.client.get<PeerStatus>('/api/peer/status'); }
  getFiles()     { return this.client.get<FileListResponse>('/api/peer/files'); }
  shareFiles(directory?: string) {
    return this.client.post<ShareFilesResponse>('/api/peer/share', directory ? { directory } : {});
  }
  downloadFile(request: DownloadRequest) {
    return this.client.post<TransferInfo>('/api/peer/download', request);
  }
  getTransfers() { return this.client.get<TransferListResponse>('/api/peer/transfers'); }
  getTransfer(transferId: string) {
    return this.client.get<TransferInfo>(`/api/peer/transfers/${transferId}`);
  }
  cancelTransfer(transferId: string) {
    return this.client.post<CancelTransferResponse>(`/api/peer/transfers/${transferId}/cancel`);
  }
  refreshFiles() { return this.client.post<ShareFilesResponse>('/api/peer/refresh'); }
}
