import { FileDown, FileUp, ArrowUpDown } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { EmptyState } from '../ui/EmptyState';
import { formatBytes, formatRelativeTime } from '../../utils/format';
import { ProgressBar } from '../transfers/ProgressBar';
import type { TransferInfo } from '../../types/transfer';

interface Props {
  transfers: TransferInfo[];
  loading: boolean;
}

export function RecentTransfers({ transfers, loading }: Props) {
  return (
    <div className="glass-panel rounded-2xl border border-white/[0.08] p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold text-sm">Transfer Pipeline</h3>
          <p className="text-[11px] text-slate-400">Recent binary socket transfer activity</p>
        </div>
        <span className="text-[10px] font-mono font-medium text-slate-400 bg-white/[0.04] px-2 py-0.5 rounded-md border border-white/[0.06]">
          {transfers.length} total
        </span>
      </div>

      {loading ? (
        <LoadingSkeleton variant="table" count={4} />
      ) : transfers.length === 0 ? (
        <EmptyState
          icon={<ArrowUpDown className="w-8 h-8" />}
          title="No transfer history"
          description="Initiate a transfer from File Explorer to monitor progress."
        />
      ) : (
        <div className="divide-y divide-white/[0.05]">
          {transfers.slice(0, 5).map(t => (
            <div
              key={t.transfer_id}
              className="flex items-center gap-3.5 py-3 hover:bg-white/[0.02] px-2 rounded-xl transition-colors"
            >
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                  t.direction === 'download'
                    ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.1)]'
                    : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.1)]'
                }`}
              >
                {t.direction === 'download' ? (
                  <FileDown className="w-4.5 h-4.5" />
                ) : (
                  <FileUp className="w-4.5 h-4.5" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-100 truncate">{t.filename}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-slate-400 font-mono">
                    {formatBytes(t.bytes_transferred)} / {formatBytes(t.total_bytes)}
                  </span>
                  {(t.status === 'downloading' || t.status === 'connecting') && (
                    <div className="flex-1 max-w-28">
                      <ProgressBar percent={t.progress_percent} status={t.status} size="sm" />
                    </div>
                  )}
                </div>
              </div>

              <div className="shrink-0 flex flex-col items-end gap-1">
                <StatusBadge status={t.status} size="sm" />
                <span className="text-[10px] text-slate-500 font-mono">
                  {formatRelativeTime(t.started_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
