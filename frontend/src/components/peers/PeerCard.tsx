import { Users, Globe, FileText, Clock } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { formatRelativeTime } from '../../utils/format';
import type { PeerInfo } from '../../types/peer';

interface Props {
  peer: PeerInfo;
  onViewFiles?: (peerId: string) => void;
}

export function PeerCard({ peer, onViewFiles }: Props) {
  return (
    <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-4 hover:border-[#3a3d4a] transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${peer.status === 'online' ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <h4 className="text-gray-100 font-semibold text-sm truncate max-w-40">{peer.peer_id}</h4>
        </div>
        <StatusBadge status={peer.status} />
      </div>
      <div className="space-y-2 text-xs text-gray-400">
        <div className="flex items-center gap-2"><Globe className="w-3.5 h-3.5 text-gray-500" /> {peer.host}:{peer.tcp_port}</div>
        <div className="flex items-center gap-2"><FileText className="w-3.5 h-3.5 text-gray-500" /> {peer.file_count} shared files</div>
        <div className="flex items-center gap-2"><Clock className="w-3.5 h-3.5 text-gray-500" /> {formatRelativeTime(peer.last_seen)}</div>
      </div>
      {onViewFiles && (
        <button onClick={() => onViewFiles(peer.peer_id)} className="mt-3 w-full py-1.5 text-xs text-gray-400 hover:text-blue-400 bg-[#0f1117] hover:bg-blue-500/10 rounded-lg transition-colors">
          View Files
        </button>
      )}
    </div>
  );
}
