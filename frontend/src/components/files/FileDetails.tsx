import { useState } from 'react';
import { Modal } from '../ui/Modal';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { StatusBadge } from '../ui/StatusBadge';
import { formatBytes, formatTimestamp } from '../../utils/format';
import { Copy, Download, Check, ShieldCheck, HardDrive } from 'lucide-react';
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
  const [copied, setCopied] = useState(false);

  if (!file) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(file.checksum);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Modal isOpen={!!file} onClose={onClose} title="File Metadata & Sources" size="lg">
      <div className="space-y-5">
        {/* File Metadata Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="glass-card p-3.5 rounded-xl border border-white/[0.06]">
            <p className="text-slate-400 text-[11px] mb-1">Target Filename</p>
            <p className="text-white font-medium text-sm truncate font-mono">{file.filename}</p>
          </div>
          <div className="glass-card p-3.5 rounded-xl border border-white/[0.06]">
            <p className="text-slate-400 text-[11px] mb-1">Total Binary Size</p>
            <p className="text-cyan-300 font-medium text-sm font-mono">{formatBytes(file.size)}</p>
          </div>
          <div className="sm:col-span-2 glass-card p-3.5 rounded-xl border border-white/[0.06]">
            <div className="flex items-center justify-between mb-1.5">
              <span className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                SHA-256 Cryptographic Checksum
              </span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-[10px] text-cyan-400 hover:text-cyan-300 font-mono transition-colors"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                {copied ? 'Copied' : 'Copy Hash'}
              </button>
            </div>
            <code className="block text-[11px] text-slate-200 bg-slate-950/60 p-2.5 rounded-lg font-mono break-all border border-white/[0.04]">
              {file.checksum}
            </code>
          </div>
          <div className="glass-card p-3.5 rounded-xl border border-white/[0.06]">
            <p className="text-slate-400 text-[11px] mb-1">Indexed At</p>
            <p className="text-slate-300 font-mono text-[11px]">{formatTimestamp(file.shared_at)}</p>
          </div>
          <div className="glass-card p-3.5 rounded-xl border border-white/[0.06]">
            <p className="text-slate-400 text-[11px] mb-1">Internal File ID</p>
            <p className="text-slate-400 font-mono text-[11px] truncate">{file.file_id}</p>
          </div>
        </div>

        {/* Available Peers List */}
        <div className="border-t border-white/[0.08] pt-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-white font-medium text-xs tracking-wide uppercase">
              Host Peers ({peers.length})
            </h4>
            <span className="text-[11px] text-slate-400">Direct TCP endpoints</span>
          </div>

          {loading ? (
            <LoadingSkeleton variant="table" count={2} />
          ) : peers.length === 0 ? (
            <div className="text-center py-6 glass-card rounded-xl border border-white/[0.06]">
              <HardDrive className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              <p className="text-slate-400 text-xs">No active peers currently host this file.</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {peers.map(p => (
                <div
                  key={p.peer_id}
                  className="flex items-center justify-between p-3 rounded-xl glass-card border border-white/[0.06] hover:border-cyan-500/30 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-medium text-white">{p.peer_id}</span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {p.host}:{p.tcp_port}
                    </span>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <button
                    onClick={() => onDownload(p.peer_id)}
                    className="glass-button-primary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-white rounded-lg font-medium shadow-sm transition-transform hover:scale-105"
                  >
                    <Download className="w-3.5 h-3.5" /> Pull from Node
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
