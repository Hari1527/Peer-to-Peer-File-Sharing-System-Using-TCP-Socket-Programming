import { Users, FileText, Zap, HardDriveDownload } from 'lucide-react';
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
    {
      label: 'Online Peers',
      value: stats?.peers_online ?? 0,
      icon: Users,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.2)]',
      meta: 'Active network nodes',
    },
    {
      label: 'Shared Catalog',
      value: stats?.total_files ?? 0,
      icon: FileText,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.2)]',
      meta: 'Indexed SHA-256 files',
    },
    {
      label: 'Active Transfers',
      value: peerStatus?.active_transfers ?? 0,
      icon: Zap,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.2)]',
      meta: 'Concurrent TCP streams',
    },
    {
      label: 'Data Streamed',
      value: formatBytes(stats?.bytes_transferred ?? 0),
      icon: HardDriveDownload,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]',
      meta: `${stats?.total_transfers ?? 0} total audits`,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4.5">
      {cards.map(c => (
        <div
          key={c.label}
          className="glass-card glass-card-hover rounded-2xl p-5 border border-white/[0.08] relative overflow-hidden group"
        >
          {/* Subtle ambient corner gradient */}
          <div className="absolute -top-12 -right-12 w-24 h-24 bg-white/[0.02] rounded-full blur-xl pointer-events-none group-hover:bg-cyan-500/[0.05] transition-all" />

          <div className="flex items-center justify-between mb-3.5">
            <span className="text-[11px] font-semibold text-slate-400 tracking-wider uppercase">
              {c.label}
            </span>
            <div className={`p-2.5 rounded-xl border ${c.bg} transition-transform group-hover:scale-105`}>
              <c.icon className={`w-4.5 h-4.5 ${c.color}`} />
            </div>
          </div>

          <div className="flex items-baseline justify-between">
            <p className="text-2xl font-bold tracking-tight text-white font-mono">
              {c.value}
            </p>
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-normal">{c.meta}</p>
        </div>
      ))}
    </div>
  );
}
