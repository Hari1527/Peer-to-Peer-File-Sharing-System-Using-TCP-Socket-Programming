import { Users, FileText, Zap, CheckCircle2 } from 'lucide-react';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { formatBytes } from '../../utils/format';
import type { TrackerStats } from '../../types/events';
import type { PeerStatus } from '../../types/peer';

interface Props {
  stats: TrackerStats | null;
  peerStatus: PeerStatus | null;
  loading: boolean;
}

export function StatsCards({ stats, peerStatus, loading }: Props) {
  if (loading) return <LoadingSkeleton variant="stat" count={4} />;

  const cards = [
    { label: 'Online Peers', value: stats?.peers_online ?? 0, icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Shared Files', value: stats?.total_files ?? 0, icon: FileText, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Active Transfers', value: peerStatus?.active_transfers ?? 0, icon: Zap, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { label: 'Total Transferred', value: formatBytes(stats?.bytes_transferred ?? 0), icon: CheckCircle2, color: 'text-cyan-400', bg: 'bg-cyan-500/10', isString: true },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(c => (
        <div key={c.label} className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{c.label}</span>
            <div className={`p-2 rounded-lg ${c.bg}`}>
              <c.icon className={`w-4 h-4 ${c.color}`} />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-100">{c.isString ? c.value : String(c.value)}</p>
        </div>
      ))}
    </div>
  );
}
