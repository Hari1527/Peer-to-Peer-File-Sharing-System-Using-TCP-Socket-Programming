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
    <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5">
      <h3 className="text-gray-100 font-semibold mb-4">Recent Transfers</h3>
      {loading ? (
        <LoadingSkeleton variant="table" count={4} />
      ) : transfers.length === 0 ? (
        <EmptyState icon={<ArrowUpDown className="w-10 h-10" />} title="No transfers yet" description="Download a file from the File Explorer to get started." />
      ) : (
        <div className="space-y-3">
          {transfers.slice(0, 5).map(t => (
            <div key={t.transfer_id} className="flex items-center gap-3 py-2 border-b border-[#2a2d3a] last:border-0">
              {t.direction === 'download' ? <FileDown className="w-4 h-4 text-blue-400 shrink-0" /> : <FileUp className="w-4 h-4 text-emerald-400 shrink-0" />}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate">{t.filename}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500">{formatBytes(t.bytes_transferred)} / {formatBytes(t.total_bytes)}</span>
                  {(t.status === 'downloading' || t.status === 'connecting') && (
                    <div className="flex-1 max-w-24"><ProgressBar percent={t.progress_percent} status={t.status} size="sm" /></div>
                  )}
                </div>
              </div>
              <div className="shrink-0 flex flex-col items-end gap-1">
                <StatusBadge status={t.status} />
                <span className="text-xs text-gray-500">{formatRelativeTime(t.started_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
