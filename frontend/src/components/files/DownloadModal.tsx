import { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { StatusBadge } from '../ui/StatusBadge';
import { formatBytes, truncateHash } from '../../utils/format';
import { Download, Loader2, Server, HardDrive } from 'lucide-react';
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

export function DownloadModal({
  isOpen,
  onClose,
  file,
  peers,
  onStartDownload,
  downloading,
}: Props) {
  const [selectedPeer, setSelectedPeer] = useState<string>('');

  const onlinePeers = peers.filter(p => p.status === 'online');

  // Auto-select first available peer
  useEffect(() => {
    if (onlinePeers.length > 0 && !selectedPeer) {
      setSelectedPeer(onlinePeers[0].peer_id);
    }
  }, [onlinePeers, selectedPeer]);

  if (!file) return null;

  const handleDownload = () => {
    if (!selectedPeer || !file) return;
    onStartDownload({ file_id: file.file_id, peer_id: selectedPeer, filename: file.filename });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Initiate P2P TCP Download">
      <div className="space-y-4.5">
        {/* File summary banner */}
        <div className="glass-card rounded-xl p-3.5 border border-white/[0.08] space-y-1">
          <p className="text-white font-medium text-xs font-mono truncate">{file.filename}</p>
          <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
            <span>Size: {formatBytes(file.size)}</span>
            <span>•</span>
            <span>SHA-256: {truncateHash(file.checksum)}</span>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-2">
            Select Source Node
          </label>
          {onlinePeers.length === 0 ? (
            <div className="text-center py-6 glass-card rounded-xl border border-white/[0.06]">
              <HardDrive className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              <p className="text-slate-400 text-xs">No online peers currently host this file.</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
              {onlinePeers.map(p => {
                const isSelected = selectedPeer === p.peer_id;
                return (
                  <label
                    key={p.peer_id}
                    className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all border ${
                      isSelected
                        ? 'bg-cyan-500/15 border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                        : 'glass-card border-white/[0.06] hover:border-white/20'
                    }`}
                  >
                    <input
                      type="radio"
                      name="peer"
                      value={p.peer_id}
                      checked={isSelected}
                      onChange={() => setSelectedPeer(p.peer_id)}
                      className="accent-cyan-400 w-4 h-4 cursor-pointer"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white font-mono truncate">{p.peer_id}</p>
                      <p className="text-[10px] text-slate-400 font-mono">
                        {p.host}:{p.tcp_port}
                      </p>
                    </div>
                    <StatusBadge status={p.status} size="sm" />
                  </label>
                );
              })}
            </div>
          )}
        </div>

        {/* Modal actions */}
        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-white/[0.08]">
          <button
            onClick={onClose}
            className="glass-button px-4 py-2 text-xs text-slate-300 hover:text-white rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleDownload}
            disabled={!selectedPeer || downloading}
            className="glass-button-primary inline-flex items-center gap-2 px-5 py-2 text-xs font-medium text-white rounded-xl shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {downloading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Connecting TCP Socket...
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" />
                Start TCP Transfer
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
}
