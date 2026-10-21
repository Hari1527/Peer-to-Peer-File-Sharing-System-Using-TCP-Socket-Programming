import { WifiOff, ShieldCheck, ArrowRight, Activity, Terminal } from 'lucide-react';
import { useAppContext, useTrackerApi } from '../context/AppContext';
import { useApi, useInterval } from '../hooks/useApi';
import { StatsCards } from '../components/dashboard/StatsCards';
import { RecentTransfers } from '../components/dashboard/RecentTransfers';
import { PeersList } from '../components/dashboard/PeersList';
import { REFRESH_INTERVAL } from '../utils/constants';
import { Link } from 'react-router-dom';

export default function OverviewPage() {
  const { state } = useAppContext();
  const trackerApi = useTrackerApi();

  const peers = useApi(() => trackerApi.getPeers('online'), []);
  const transfers = useApi(() => trackerApi.getTransfers(20), []);

  useInterval(() => {
    peers.refetch();
    transfers.refetch();
  }, REFRESH_INTERVAL);

  const isDisconnected = !state.trackerConnected || !state.peerConnected;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Network Alert Banner */}
      {isDisconnected && (
        <div className="glass-panel border-amber-500/30 bg-amber-950/20 rounded-2xl p-4.5 flex items-start sm:items-center gap-3.5 shadow-[0_0_25px_rgba(245,158,11,0.1)]">
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 shrink-0 border border-amber-500/20">
            <WifiOff className="w-5 h-5" />
          </div>
          <div className="flex-1 text-xs">
            <h4 className="text-white font-semibold text-xs mb-1">Decentralized Mesh Degraded</h4>
            {!state.trackerConnected && (
              <p className="text-amber-200/80 mb-0.5">
                • Central Tracker registry is unreachable at <code className="font-mono text-amber-300">{state.trackerUrl}</code>. Run <code className="font-mono bg-black/40 px-1 py-0.5 rounded">python3 scripts/start_tracker.py</code>.
              </p>
            )}
            {!state.peerConnected && (
              <p className="text-amber-200/80">
                • Local peer node is disconnected at <code className="font-mono text-amber-300">{state.peerUrl}</code>. Run <code className="font-mono bg-black/40 px-1 py-0.5 rounded">python3 scripts/start_peer.py</code>.
              </p>
            )}
          </div>
          <Link
            to="/settings"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs text-amber-300 hover:text-white glass-button px-3 py-1.5 rounded-xl border border-amber-500/30 shrink-0"
          >
            Configure <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Primary Metrics Grid */}
      <StatsCards
        stats={state.trackerStats}
        peerStatus={state.peerStatus}
        loading={!state.trackerConnected && !state.trackerStats}
      />

      {/* Main Content Split: Pipeline & Active Peers */}
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
