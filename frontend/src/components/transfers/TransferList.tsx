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

const tabs = ['all', 'active', 'completed', 'failed', 'cancelled'];

export function TransferList({ transfers, loading, filter, onFilterChange, onCancel }: Props) {
  const filtered = filter === 'all' ? transfers
    : filter === 'active' ? transfers.filter(t => ['pending', 'connecting', 'downloading', 'verifying'].includes(t.status))
    : transfers.filter(t => t.status === filter);

  return (
    <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a]">
      <div className="flex items-center gap-1 px-4 pt-4 pb-2 border-b border-[#2a2d3a] overflow-x-auto">
        {tabs.map(tab => (
          <button key={tab} onClick={() => onFilterChange(tab)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
              filter === tab ? 'bg-blue-500/10 text-blue-400' : 'text-gray-500 hover:text-gray-300 hover:bg-[#2a2d3a]'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === 'all' && <span className="ml-1 text-gray-500">({transfers.length})</span>}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="p-4"><LoadingSkeleton variant="table" count={4} /></div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={<ArrowUpDown className="w-10 h-10" />} title="No transfers" description={`No ${filter === 'all' ? '' : filter + ' '}transfers to show.`} />
      ) : (
        <div>{filtered.map(t => <TransferRow key={t.transfer_id} transfer={t} onCancel={onCancel} />)}</div>
      )}
    </div>
  );
}
