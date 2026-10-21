import { useState, useCallback } from 'react';
import { RefreshCw, FolderSearch, HardDrive, Shield } from 'lucide-react';
import { useAppContext, useTrackerApi, usePeerApi } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import { FileTable } from '../components/files/FileTable';
import { FileDetails } from '../components/files/FileDetails';
import { DownloadModal } from '../components/files/DownloadModal';
import { SearchInput } from '../components/ui/SearchInput';
import { ErrorState } from '../components/ui/ErrorState';
import type { SharedFileInfo } from '../types/file';
import type { PeerInfo } from '../types/peer';
import type { DownloadRequest } from '../types/transfer';

export default function FilesPage() {
  const { addNotification } = useAppContext();
  const trackerApi = useTrackerApi();
  const peerApi = usePeerApi();

  const [search, setSearch] = useState('');
  const [selectedFile, setSelectedFile] = useState<SharedFileInfo | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showDownload, setShowDownload] = useState(false);
  const [filePeers, setFilePeers] = useState<PeerInfo[]>([]);
  const [loadingPeers, setLoadingPeers] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchFiles = useCallback(() => {
    return search.trim() ? trackerApi.searchFiles(search.trim()) : trackerApi.getFiles();
  }, [search, trackerApi]);

  const files = useApi(fetchFiles, [search]);

  const handleViewPeers = async (file: SharedFileInfo) => {
    setSelectedFile(file);
    setShowDetails(true);
    setLoadingPeers(true);
    try {
      const res = await trackerApi.getFilePeers(file.file_id);
      setFilePeers(res.peers);
    } catch {
      setFilePeers([]);
    }
    setLoadingPeers(false);
  };

  const handleOpenDownload = async (file: SharedFileInfo) => {
    setSelectedFile(file);
    setLoadingPeers(true);
    try {
      const res = await trackerApi.getFilePeers(file.file_id);
      setFilePeers(res.peers);
    } catch {
      setFilePeers([]);
    }
    setLoadingPeers(false);
    setShowDownload(true);
  };

  const handleDownload = async (request: DownloadRequest) => {
    setDownloading(true);
    try {
      await peerApi.downloadFile(request);
      addNotification('success', `Direct TCP download initiated: ${request.filename}`);
      setShowDownload(false);
    } catch (err) {
      addNotification('error', `Download failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
    setDownloading(false);
  };

  const handleDownloadFromDetails = (peerId: string) => {
    if (!selectedFile) return;
    setShowDetails(false);
    handleDownload({ file_id: selectedFile.file_id, peer_id: peerId, filename: selectedFile.filename });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await peerApi.refreshFiles();
      addNotification('success', 'Local shared directory re-indexed');
      files.refetch();
    } catch (err) {
      addNotification('error', `Refresh failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
    setRefreshing(false);
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="w-full sm:max-w-md">
          <SearchInput value={search} onChange={setSearch} placeholder="Search indexed files by name..." />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="glass-button inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-slate-200 hover:text-white rounded-xl transition-all shadow-sm"
            title="Scan local directory and update tracker index"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Scan Directory</span>
          </button>
        </div>
      </div>

      {/* Main File Table Glass Panel */}
      {files.error ? (
        <ErrorState message={files.error} onRetry={files.refetch} />
      ) : (
        <div className="glass-panel rounded-2xl border border-white/[0.08] shadow-2xl overflow-hidden">
          <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
            <div className="flex items-center gap-2">
              <FolderSearch className="w-4 h-4 text-cyan-400" />
              <h3 className="text-white font-semibold text-xs tracking-wide uppercase">
                Decentralized Catalog
              </h3>
            </div>
            <span className="text-[11px] font-mono font-medium text-slate-400 bg-white/[0.04] px-2.5 py-1 rounded-md border border-white/[0.06]">
              {files.data?.total ?? 0} files indexed
            </span>
          </div>

          <FileTable
            files={files.data?.files ?? []}
            loading={files.loading}
            onViewPeers={handleViewPeers}
            onDownload={handleOpenDownload}
            emptyMessage={search ? `No files matching "${search}" found.` : undefined}
          />
        </div>
      )}

      {/* Modals */}
      <FileDetails
        file={selectedFile}
        peers={filePeers}
        onDownload={handleDownloadFromDetails}
        onClose={() => setShowDetails(false)}
        loading={loadingPeers}
      />

      <DownloadModal
        isOpen={showDownload}
        onClose={() => setShowDownload(false)}
        file={selectedFile}
        peers={filePeers}
        onStartDownload={handleDownload}
        downloading={downloading}
      />
    </div>
  );
}
