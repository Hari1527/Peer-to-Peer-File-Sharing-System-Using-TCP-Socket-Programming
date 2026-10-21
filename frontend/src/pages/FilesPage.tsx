import { useState, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
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
    } catch { setFilePeers([]); }
    setLoadingPeers(false);
  };

  const handleOpenDownload = async (file: SharedFileInfo) => {
    setSelectedFile(file);
    setLoadingPeers(true);
    try {
      const res = await trackerApi.getFilePeers(file.file_id);
      setFilePeers(res.peers);
    } catch { setFilePeers([]); }
    setLoadingPeers(false);
    setShowDownload(true);
  };

  const handleDownload = async (request: DownloadRequest) => {
    setDownloading(true);
    try {
      await peerApi.downloadFile(request);
      addNotification('success', `Download started: ${request.filename}`);
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
    try {
      await peerApi.refreshFiles();
      addNotification('success', 'Files refreshed');
      files.refetch();
    } catch (err) {
      addNotification('error', `Refresh failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="flex-1 w-full sm:max-w-sm">
          <SearchInput value={search} onChange={setSearch} placeholder="Search files..." />
        </div>
        <button onClick={handleRefresh} className="inline-flex items-center gap-2 px-3 py-2 bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 text-sm rounded-lg transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {files.error ? (
        <ErrorState message={files.error} onRetry={files.refetch} />
      ) : (
        <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a]">
          <div className="px-5 py-3 border-b border-[#2a2d3a] flex items-center justify-between">
            <h3 className="text-gray-200 font-medium text-sm">Shared Files</h3>
            <span className="text-xs text-gray-500">{files.data?.total ?? 0} files</span>
          </div>
          <FileTable files={files.data?.files ?? []} loading={files.loading} onViewPeers={handleViewPeers} onDownload={handleOpenDownload} />
        </div>
      )}

      <FileDetails file={selectedFile} peers={filePeers} onDownload={handleDownloadFromDetails} onClose={() => setShowDetails(false)} loading={loadingPeers} />
      <DownloadModal isOpen={showDownload} onClose={() => setShowDownload(false)} file={selectedFile} peers={filePeers} onStartDownload={handleDownload} downloading={downloading} />
    </div>
  );
}
