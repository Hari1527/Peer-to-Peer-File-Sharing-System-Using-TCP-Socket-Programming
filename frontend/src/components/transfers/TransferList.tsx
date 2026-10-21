import { ArrowUpDown } from 'lucide-react';
import { TransferRow } from './TransferRow';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { EmptyState } from '../ui/EmptyState';
import type { TransferInfo } from '../../types/transfer';

interface Props {
  transfers: TransferInfo[];
  loading: boolean;
  filter: string;
  onFilterChange: (filter: string) => void;
  onCancel?: (transferId: string) => void;
}

const tabs = ['all', 'active', 'completed', 'failed', 'cancelled'] as const;

export function TransferList({
  transfers,
  loading,
  filter,
  onFilterChange,
  onCancel,
}: Props) {
  const filtered =
    filter === 'all'
      ? transfers
      : filter === 'active'
      ? transfers.filter(t =>
          ['pending', 'connecting', 'downloading', 'verifying'].includes(t.status)
        )
      : transfers.filter(t => t.status === filter);

  return (
    <div className="glass-panel rounded-2xl border border-white/[0.08] overflow-hidden shadow-2xl">
      {/* Tab Filter Header */}
      <div className="flex items-center gap-1.5 p-3.5 border-b border-white/[0.08] bg-white/[0.02] overflow-x-auto">
        {tabs.map(tab => {
          const isActive = filter === tab;
          const count =
            tab === 'all'
              ? transfers.length
              : tab === 'active'
              ? transfers.filter(t =>
                  ['pending', 'connecting', 'downloading', 'verifying'].includes(t.status)
                ).length
              : transfers.filter(t => t.status === tab).length;

          return (
            <button
              key={tab}
              onClick={() => onFilterChange(tab)}
              className={`px-3.5 py-1.5 text-xs font-medium rounded-xl whitespace-nowrap transition-all flex items-center gap-2 ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.15)]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.05] border border-transparent'
              }`}
            >
              <span className="capitalize">{tab}</span>
              <span
                className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                  isActive ? 'bg-cyan-500/20 text-cyan-200' : 'bg-white/[0.06] text-slate-500'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="p-4">
          <LoadingSkeleton variant="table" count={5} />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<ArrowUpDown className="w-9 h-9" />}
          title={`No ${filter === 'all' ? '' : filter + ' '}transfers recorded`}
          description={
            filter === 'active'
              ? 'There are currently no active socket downloads running.'
              : 'Transfers initiated between network peers will appear here.'
          }
        />
      ) : (
        <div className="divide-y divide-white/[0.05]">
          {filtered.map(t => (
            <TransferRow key={t.transfer_id} transfer={t} onCancel={onCancel} />
          ))}
        </div>
      )}
    </div>
  );
}
