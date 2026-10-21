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
  if (loading) return <LoadingSkeleton variant="card" count={3} />;
  if (peers.length === 0) return <EmptyState icon={<Users className="w-12 h-12" />} title="No peers found" description="Start a peer agent to join the network." />;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {peers.map(p => <PeerCard key={p.peer_id} peer={p} onViewFiles={onViewFiles} />)}
    </div>
  );
}
