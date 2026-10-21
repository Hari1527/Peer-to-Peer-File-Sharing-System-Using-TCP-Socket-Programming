import { Users } from 'lucide-react';
import { PeerCard } from './PeerCard';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { EmptyState } from '../ui/EmptyState';
import type { PeerInfo } from '../../types/peer';

interface Props {
  peers: PeerInfo[];
  loading: boolean;
  onViewFiles?: (peerId: string) => void;
}

export function PeerGrid({ peers, loading, onViewFiles }: Props) {
  if (loading) return <LoadingSkeleton variant="card" count={6} />;
  if (peers.length === 0)
    return (
      <EmptyState
        icon={<Users className="w-10 h-10" />}
        title="No peers discovered in topology"
        description="Launch a peer agent node with start_peer.py to register."
      />
    );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4.5">
      {peers.map(p => (
        <PeerCard key={p.peer_id} peer={p} onViewFiles={onViewFiles} />
      ))}
    </div>
  );
}
