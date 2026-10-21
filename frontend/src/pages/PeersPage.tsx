import { useState } from 'react';
import { RefreshCw, Users } from 'lucide-react';
import { useTrackerApi } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import { PeerGrid } from '../components/peers/PeerGrid';
import { ErrorState } from '../components/ui/ErrorState';
import { useNavigate } from 'react-router-dom';

export default function PeersPage() {
  const trackerApi = useTrackerApi();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<string>('');

  const peers = useApi(() => trackerApi.getPeers(filter || undefined), [filter]);

  const filters = [
    { label: 'All Nodes', value: '' },
    { label: 'Online Only', value: 'online' },
    { label: 'Offline / Reaped', value: 'offline' },
  ];

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Top Filter and Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {filters.map(f => {
            const isActive = filter === f.value;
            return (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`px-3.5 py-1.5 text-xs font-medium rounded-xl transition-all ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.15)]'
                    : 'glass-button text-slate-400 hover:text-white'
                }`}
              >
                {f.label}
              </button>
            );
          })}
          <span className="text-xs text-slate-500 font-mono ml-2 hidden sm:inline">
            ({peers.data?.total ?? 0} registered)
          </span>
        </div>

        <button
          onClick={peers.refetch}
          className="glass-button inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium text-slate-200 hover:text-white rounded-xl transition-all shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Mesh</span>
        </button>
      </div>

      {/* Peer Grid */}
      {peers.error ? (
        <ErrorState message={peers.error} onRetry={peers.refetch} />
      ) : (
        <PeerGrid
          peers={peers.data?.peers ?? []}
          loading={peers.loading}
          onViewFiles={peerId => navigate(`/files?peer=${peerId}`)}
        />
      )}
    </div>
  );
}
