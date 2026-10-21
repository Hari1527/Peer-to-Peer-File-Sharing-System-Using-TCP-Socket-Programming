import { Globe, FileText, Clock, HardDrive, ArrowUpRight } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { formatRelativeTime } from '../../utils/format';
import type { PeerInfo } from '../../types/peer';

interface Props {
  peer: PeerInfo;
  onViewFiles?: (peerId: string) => void;
}

export function PeerCard({ peer, onViewFiles }: Props) {
  const isOnline = peer.status === 'online';

  return (
    <div className="glass-card glass-card-hover rounded-2xl border border-white/[0.08] p-5 relative overflow-hidden group">
      {/* Ambient status glow */}
      <div
        className={`absolute -top-10 -right-10 w-24 h-24 rounded-full blur-2xl pointer-events-none transition-opacity ${
          isOnline ? 'bg-emerald-500/10' : 'bg-rose-500/10'
        }`}
      />

      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-9 h-9 rounded-xl glass-panel flex items-center justify-center shrink-0 border border-white/[0.08]">
            <HardDrive className={`w-4.5 h-4.5 ${isOnline ? 'text-cyan-400' : 'text-slate-500'}`} />
          </div>
          <div className="min-w-0">
            <h4 className="text-white font-mono font-semibold text-xs truncate max-w-[10rem]">
              {peer.peer_id}
            </h4>
            <span className="text-[10px] text-slate-400 font-mono">
              TCP Port {peer.tcp_port}
            </span>
          </div>
        </div>
        <StatusBadge status={peer.status} size="sm" />
      </div>

      <div className="space-y-2.5 text-xs text-slate-300 mb-4 bg-slate-950/40 p-3 rounded-xl border border-white/[0.04]">
        <div className="flex items-center justify-between text-[11px] font-mono">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Globe className="w-3.5 h-3.5 text-slate-500" /> Endpoint
          </span>
          <span className="text-slate-200">
            {peer.host}:{peer.tcp_port}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] font-mono">
          <span className="flex items-center gap-1.5 text-slate-400">
            <FileText className="w-3.5 h-3.5 text-slate-500" /> Files Shared
          </span>
          <span className="text-cyan-300 font-medium">{peer.file_count}</span>
        </div>
        <div className="flex items-center justify-between text-[11px] font-mono">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Clock className="w-3.5 h-3.5 text-slate-500" /> Heartbeat
          </span>
          <span className="text-slate-400">{formatRelativeTime(peer.last_seen)}</span>
        </div>
      </div>

      {onViewFiles && (
        <button
          onClick={() => onViewFiles(peer.peer_id)}
          className="w-full glass-button py-2 text-xs font-medium text-slate-300 hover:text-white rounded-xl transition-all flex items-center justify-center gap-1.5 group-hover:border-cyan-500/30"
        >
          <span>Explore Files</span>
          <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-400 transition-colors" />
        </button>
      )}
    </div>
  );
}
