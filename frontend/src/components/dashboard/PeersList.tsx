import { Users, Globe } from 'lucide-react';
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
    <div className="glass-panel rounded-2xl border border-white/[0.08] p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold text-sm">Active Mesh Peers</h3>
          <p className="text-[11px] text-slate-400">Discoverable transfer targets</p>
        </div>
        <span className="text-[10px] font-mono font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
          {peers.length} online
        </span>
      </div>

      {loading ? (
        <LoadingSkeleton variant="table" count={3} />
      ) : peers.length === 0 ? (
        <EmptyState
          icon={<Users className="w-8 h-8" />}
          title="No peers discovered"
          description="Start peer agents on ports 9001/9002 to join network."
        />
      ) : (
        <div className="space-y-2">
          {peers.map(p => (
            <div
              key={p.peer_id}
              className="flex items-center gap-3 py-2.5 px-3 rounded-xl glass-card border border-white/[0.05] hover:border-cyan-500/30 transition-all"
            >
              <div className="relative">
                <div
                  className={`w-2.5 h-2.5 rounded-full ${
                    p.status === 'online'
                      ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                      : 'bg-rose-400'
                  }`}
                />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-100 font-mono truncate">{p.peer_id}</p>
                <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
                  <Globe className="w-3 h-3 text-slate-500" />
                  <span>
                    {p.host}:{p.tcp_port}
                  </span>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[10px] text-cyan-300 font-mono bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                  {p.file_count} files
                </span>
                <p className="text-[10px] text-slate-500 mt-1 font-mono">
                  {formatRelativeTime(p.last_seen)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
