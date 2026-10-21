import { useState } from 'react';
import { RefreshCw, ArrowUpDown, HardDrive, Globe } from 'lucide-react';
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

  // Poll active transfers every 3s
  useInterval(() => {
    current.refetch();
  }, ACTIVE_REFRESH_INTERVAL);

  const handleCancel = async (transferId: string) => {
    try {
      await peerApi.cancelTransfer(transferId);
      addNotification('info', 'Transfer cancelled gracefully');
      localTransfers.refetch();
    } catch (err) {
      addNotification(
        'error',
        `Cancel failed: ${err instanceof Error ? err.message : 'Unknown error'}`
      );
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Scope Switcher & Header Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 p-1 glass-card rounded-2xl border border-white/[0.08] w-fit">
          <button
            onClick={() => setTab('local')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
              tab === 'local'
                ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.2)]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <HardDrive className="w-3.5 h-3.5" />
            <span>Local Node Streams</span>
          </button>
          <button
            onClick={() => setTab('global')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
              tab === 'global'
                ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.2)]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Global Tracker Audit</span>
          </button>
        </div>

        <button
          onClick={current.refetch}
          className="glass-button inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium text-slate-200 hover:text-white rounded-xl transition-all shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Sync Transfers</span>
        </button>
      </div>

      {/* Main Transfer List */}
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
