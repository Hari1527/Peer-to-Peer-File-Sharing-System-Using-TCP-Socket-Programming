import { Modal } from '../ui/Modal';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { StatusBadge } from '../ui/StatusBadge';
import { formatBytes, formatTimestamp } from '../../utils/format';
import { Copy, Download } from 'lucide-react';
import type { SharedFileInfo } from '../../types/file';
import type { PeerInfo } from '../../types/peer';

interface Props {
  file: SharedFileInfo | null;
  peers: PeerInfo[];
  onDownload: (peerId: string) => void;
  onClose: () => void;
  loading: boolean;
}

export function FileDetails({ file, peers, onDownload, onClose, loading }: Props) {
  if (!file) return null;

  return (
    <Modal isOpen={!!file} onClose={onClose} title="File Details" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-500 text-xs mb-1">Filename</p>
            <p className="text-gray-100 font-medium">{file.filename}</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Size</p>
            <p className="text-gray-100">{formatBytes(file.size)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-gray-500 text-xs mb-1">SHA-256 Checksum</p>
            <div className="flex items-center gap-2">
              <code className="text-xs text-gray-300 bg-[#0f1117] px-2 py-1 rounded font-mono break-all">{file.checksum}</code>
              <button onClick={() => navigator.clipboard.writeText(file.checksum)} className="text-gray-500 hover:text-gray-300 shrink-0"><Copy className="w-3.5 h-3.5" /></button>
            </div>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Shared At</p>
            <p className="text-gray-400 text-sm">{formatTimestamp(file.shared_at)}</p>
          </div>
        </div>

        <div className="border-t border-[#2a2d3a] pt-4">
          <h4 className="text-gray-200 font-medium text-sm mb-3">Available Peers</h4>
          {loading ? <LoadingSkeleton variant="table" count={2} /> : peers.length === 0 ? (
            <p className="text-gray-500 text-sm">No peers found for this file.</p>
          ) : (
            <div className="space-y-2">
              {peers.map(p => (
                <div key={p.peer_id} className="flex items-center justify-between py-2 px-3 rounded-lg bg-[#0f1117]">
                  <div className="flex items-center gap-3">
                    <StatusBadge status={p.status} />
                    <div>
                      <p className="text-sm text-gray-200 font-medium">{p.peer_id}</p>
                      <p className="text-xs text-gray-500">{p.host}:{p.tcp_port}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => onDownload(p.peer_id)}
                    disabled={p.status !== 'online'}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs rounded-lg transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" /> Download
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
