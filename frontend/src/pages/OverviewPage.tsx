import { WifiOff } from 'lucide-react';
import { useAppContext, useTrackerApi } from '../context/AppContext';
import { useApi, useInterval } from '../hooks/useApi';
import { StatsCards } from '../components/dashboard/StatsCards';
import { RecentTransfers } from '../components/dashboard/RecentTransfers';
import { PeersList } from '../components/dashboard/PeersList';
import { REFRESH_INTERVAL } from '../utils/constants';

export default function OverviewPage() {
  const { state } = useAppContext();
  const trackerApi = useTrackerApi();

  const peers = useApi(() => trackerApi.getPeers('online'), []);
  const transfers = useApi(() => trackerApi.getTransfers(20), []);

  useInterval(() => { peers.refetch(); transfers.refetch(); }, REFRESH_INTERVAL);

  return (
    <div className="space-y-6 animate-fade-in">
      {(!state.trackerConnected || !state.peerConnected) && (
        <div className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
          <WifiOff className="w-5 h-5 text-amber-400 shrink-0" />
          <div className="text-sm">
            {!state.trackerConnected && <p className="text-amber-300">Tracker is not connected. Ensure it's running on {state.trackerUrl}</p>}
            {!state.peerConnected && <p className="text-amber-300">Peer agent is not connected. Start it on {state.peerUrl}</p>}
          </div>
        </div>
      )}

      <StatsCards stats={state.trackerStats} peerStatus={state.peerStatus} loading={!state.trackerConnected && !state.trackerStats} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentTransfers transfers={transfers.data?.transfers ?? []} loading={transfers.loading} />
        </div>
        <div>
          <PeersList peers={peers.data?.peers ?? []} loading={peers.loading} />
        </div>
      </div>
    </div>
  );
}
