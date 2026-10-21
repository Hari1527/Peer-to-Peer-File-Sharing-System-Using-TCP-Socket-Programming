import { FileDown, FileUp, X } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { ProgressBar } from './ProgressBar';
import { formatBytes, formatSpeed, formatDuration, formatRelativeTime } from '../../utils/format';
import type { TransferInfo } from '../../types/transfer';

interface Props {
  transfer: TransferInfo;
  onCancel?: (transferId: string) => void;
}

export function TransferRow({ transfer: t, onCancel }: Props) {
  const isActive = t.status === 'downloading' || t.status === 'connecting' || t.status === 'pending' || t.status === 'verifying';

  return (
    <div className="py-3 px-4 border-b border-[#2a2d3a] hover:bg-[#1e2130] transition-colors">
      <div className="flex items-center gap-3">
        {t.direction === 'download' ? <FileDown className="w-4 h-4 text-blue-400 shrink-0" /> : <FileUp className="w-4 h-4 text-emerald-400 shrink-0" />}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm text-gray-100 font-medium truncate">{t.filename}</span>
            <StatusBadge status={t.status} />
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{t.source_peer_id.slice(0, 8)} → {t.dest_peer_id.slice(0, 8)}</span>
            <span>{formatBytes(t.bytes_transferred)} / {formatBytes(t.total_bytes)}</span>
            {t.speed_bps > 0 && <span>{formatSpeed(t.speed_bps)}</span>}
            <span>{formatDuration(t.started_at, t.completed_at)}</span>
          </div>
          {isActive && (
            <div className="mt-1.5 max-w-xs"><ProgressBar percent={t.progress_percent} status={t.status} size="md" /></div>
          )}
          {t.error_message && <p className="text-xs text-red-400 mt-1">{t.error_message}</p>}
        </div>

        <div className="shrink-0 text-right">
          <p className="text-xs text-gray-500">{formatRelativeTime(t.started_at)}</p>
          {isActive && onCancel && (
            <button onClick={() => onCancel(t.transfer_id)} className="mt-1 p-1 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors" title="Cancel">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
