import { FileDown, FileUp, X, Clock, Zap, ArrowRight } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { ProgressBar } from './ProgressBar';
import { formatBytes, formatSpeed, formatDuration, formatRelativeTime } from '../../utils/format';
import type { TransferInfo } from '../../types/transfer';

interface Props {
  transfer: TransferInfo;
  onCancel?: (transferId: string) => void;
}

export function TransferRow({ transfer: t, onCancel }: Props) {
  const isActive =
    t.status === 'downloading' ||
    t.status === 'connecting' ||
    t.status === 'pending' ||
    t.status === 'verifying';

  return (
    <div className="p-4 hover:bg-white/[0.03] transition-colors border-b border-white/[0.05] last:border-0 group">
      <div className="flex items-start sm:items-center gap-3.5">
        {/* Direction Avatar */}
        <div
          className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
            t.direction === 'download'
              ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.15)]'
              : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
          }`}
        >
          {t.direction === 'download' ? (
            <FileDown className="w-4.5 h-4.5" />
          ) : (
            <FileUp className="w-4.5 h-4.5" />
          )}
        </div>

        {/* Transfer Body */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-xs sm:text-sm text-white font-medium truncate max-w-xs font-mono">
              {t.filename}
            </span>
            <StatusBadge status={t.status} size="sm" />
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-400 font-mono">
            <span className="flex items-center gap-1 text-slate-300">
              <span>{t.source_peer_id.slice(0, 8)}</span>
              <ArrowRight className="w-3 h-3 text-slate-500" />
              <span>{t.dest_peer_id.slice(0, 8)}</span>
            </span>
            <span>
              {formatBytes(t.bytes_transferred)} / {formatBytes(t.total_bytes)}
            </span>
            {t.speed_bps > 0 && (
              <span className="text-cyan-300 flex items-center gap-1 font-semibold">
                <Zap className="w-3 h-3 text-cyan-400" />
                {formatSpeed(t.speed_bps)}
              </span>
            )}
            <span className="text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-600" />
              {formatDuration(t.started_at, t.completed_at)}
            </span>
          </div>

          {isActive && (
            <div className="mt-2.5 max-w-sm">
              <ProgressBar percent={t.progress_percent} status={t.status} size="md" />
            </div>
          )}

          {t.error_message && (
            <p className="text-[11px] text-rose-400 mt-1.5 font-mono bg-rose-500/10 p-1.5 rounded border border-rose-500/20 max-w-md">
              Error: {t.error_message}
            </p>
          )}
        </div>

        {/* Actions & Timestamps */}
        <div className="shrink-0 flex flex-col items-end gap-1.5">
          <p className="text-[10px] text-slate-500 font-mono">
            {formatRelativeTime(t.started_at)}
          </p>
          {isActive && onCancel && (
            <button
              onClick={() => onCancel(t.transfer_id)}
              className="px-2.5 py-1 text-[11px] font-mono text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-500/30 border border-rose-500/20 rounded-lg transition-all flex items-center gap-1"
              title="Abort ongoing transfer"
            >
              <X className="w-3 h-3" /> Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
