import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
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
    { label: 'All', value: '' },
    { label: 'Online', value: 'online' },
    { label: 'Offline', value: 'offline' },
  ];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {filters.map(f => (
            <button key={f.value} onClick={() => setFilter(f.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${filter === f.value ? 'bg-blue-500/10 text-blue-400' : 'text-gray-500 hover:text-gray-300 hover:bg-[#2a2d3a]'}`}>
              {f.label}
            </button>
          ))}
          <span className="text-xs text-gray-500 ml-2">{peers.data?.total ?? 0} peers</span>
        </div>
        <button onClick={peers.refetch} className="inline-flex items-center gap-2 px-3 py-2 bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 text-sm rounded-lg transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {peers.error ? (
        <ErrorState message={peers.error} onRetry={peers.refetch} />
      ) : (
        <PeerGrid peers={peers.data?.peers ?? []} loading={peers.loading} onViewFiles={(peerId) => navigate(`/files?peer=${peerId}`)} />
      )}
    </div>
  );
}
