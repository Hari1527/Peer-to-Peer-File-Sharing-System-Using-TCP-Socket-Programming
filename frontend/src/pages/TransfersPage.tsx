import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { useAppContext, useTrackerApi, usePeerApi } from '../context/AppContext';
import { useApi, useInterval } from '../hooks/useApi';
import { TransferList } from '../components/transfers/TransferList';
import { ErrorState } from '../components/ui/ErrorState';
import { ACTIVE_REFRESH_INTERVAL } from '../utils/constants';

export default function TransfersPage() {
  const { addNotification } = useAppContext();
  const trackerApi = useTrackerApi();
  const peerApi = usePeerApi();

  const [tab, setTab] = useState<'local' | 'global'>('local');
  const [filter, setFilter] = useState('all');

  const localTransfers = useApi(() => peerApi.getTransfers(), []);
  const globalTransfers = useApi(() => trackerApi.getTransfers(50), []);

  const current = tab === 'local' ? localTransfers : globalTransfers;

  useInterval(() => { current.refetch(); }, ACTIVE_REFRESH_INTERVAL);

  const handleCancel = async (transferId: string) => {
    try {
      await peerApi.cancelTransfer(transferId);
      addNotification('info', 'Transfer cancelled');
      localTransfers.refetch();
    } catch (err) {
      addNotification('error', `Cancel failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={() => setTab('local')} className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${tab === 'local' ? 'bg-blue-500/10 text-blue-400' : 'text-gray-500 hover:text-gray-300'}`}>
            Local Transfers
          </button>
          <button onClick={() => setTab('global')} className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${tab === 'global' ? 'bg-blue-500/10 text-blue-400' : 'text-gray-500 hover:text-gray-300'}`}>
            Global History
          </button>
        </div>
        <button onClick={current.refetch} className="inline-flex items-center gap-2 px-3 py-2 bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 text-sm rounded-lg transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {current.error ? (
        <ErrorState message={current.error} onRetry={current.refetch} />
      ) : (
        <TransferList
          transfers={current.data?.transfers ?? []}
          loading={current.loading}
          filter={filter}
          onFilterChange={setFilter}
          onCancel={tab === 'local' ? handleCancel : undefined}
        />
      )}
    </div>
  );
}
