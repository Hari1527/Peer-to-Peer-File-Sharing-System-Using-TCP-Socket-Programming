import { useState } from 'react';
import { Modal } from '../ui/Modal';
import { StatusBadge } from '../ui/StatusBadge';
import { formatBytes, truncateHash } from '../../utils/format';
import { Download, Loader2 } from 'lucide-react';
import type { SharedFileInfo } from '../../types/file';
import type { PeerInfo } from '../../types/peer';
import type { DownloadRequest } from '../../types/transfer';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  file: SharedFileInfo | null;
  peers: PeerInfo[];
  onStartDownload: (request: DownloadRequest) => void;
  downloading: boolean;
}

export function DownloadModal({ isOpen, onClose, file, peers, onStartDownload, downloading }: Props) {
  const [selectedPeer, setSelectedPeer] = useState<string>('');

  if (!file) return null;

  const handleDownload = () => {
    if (!selectedPeer || !file) return;
    onStartDownload({ file_id: file.file_id, peer_id: selectedPeer, filename: file.filename });
  };

  const onlinePeers = peers.filter(p => p.status === 'online');

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Download File">
      <div className="space-y-4">
        <div className="bg-[#0f1117] rounded-lg p-3 space-y-1.5">
          <p className="text-gray-100 font-medium text-sm">{file.filename}</p>
          <p className="text-gray-500 text-xs">Size: {formatBytes(file.size)} · SHA-256: {truncateHash(file.checksum)}</p>
        </div>

        <div>
          <p className="text-gray-300 text-sm font-medium mb-2">Select source peer</p>
          {onlinePeers.length === 0 ? (
            <p className="text-gray-500 text-sm">No online peers have this file.</p>
          ) : (
            <div className="space-y-2">
              {onlinePeers.map(p => (
                <label key={p.peer_id} className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${selectedPeer === p.peer_id ? 'bg-blue-500/10 border border-blue-500/30' : 'bg-[#0f1117] border border-transparent hover:border-[#2a2d3a]'}`}>
                  <input type="radio" name="peer" value={p.peer_id} checked={selectedPeer === p.peer_id} onChange={() => setSelectedPeer(p.peer_id)} className="accent-blue-500" />
                  <div className="flex-1">
                    <p className="text-sm text-gray-200">{p.peer_id}</p>
                    <p className="text-xs text-gray-500">{p.host}:{p.tcp_port}</p>
                  </div>
                  <StatusBadge status={p.status} />
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-[#2a2d3a]">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">Cancel</button>
          <button onClick={handleDownload} disabled={!selectedPeer || downloading} className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors">
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {downloading ? 'Starting...' : 'Download'}
          </button>
        </div>
      </div>
    </Modal>
  );
}
