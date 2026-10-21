import { Users } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { EmptyState } from '../ui/EmptyState';
import { formatRelativeTime } from '../../utils/format';
import type { PeerInfo } from '../../types/peer';

interface Props {
  peers: PeerInfo[];
  loading: boolean;
}

export function PeersList({ peers, loading }: Props) {
  return (
    <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5">
      <h3 className="text-gray-100 font-semibold mb-4">Connected Peers</h3>
      {loading ? (
        <LoadingSkeleton variant="table" count={3} />
      ) : peers.length === 0 ? (
        <EmptyState icon={<Users className="w-10 h-10" />} title="No peers online" description="Start a peer agent to see it here." />
      ) : (
        <div className="space-y-2">
          {peers.map(p => (
            <div key={p.peer_id} className="flex items-center gap-3 py-2.5 px-3 rounded-lg hover:bg-[#1e2130] transition-colors">
              <span className={`w-2 h-2 rounded-full shrink-0 ${p.status === 'online' ? 'bg-emerald-400' : 'bg-red-400'}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 font-medium truncate">{p.peer_id}</p>
                <p className="text-xs text-gray-500">{p.host}:{p.tcp_port}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-gray-400">{p.file_count} files</p>
                <p className="text-xs text-gray-500">{formatRelativeTime(p.last_seen)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
