import { Menu, Server, HardDrive } from 'lucide-react';
import type { PeerStatus } from '../../types/peer';

interface Props {
  title: string;
  trackerConnected: boolean;
  peerConnected: boolean;
  peerStatus: PeerStatus | null;
  onMenuToggle: () => void;
}

export function TopBar({ title, trackerConnected, peerConnected, peerStatus, onMenuToggle }: Props) {
  return (
    <header className="h-14 bg-[#161922] border-b border-[#2a2d3a] flex items-center justify-between px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <button onClick={onMenuToggle} className="lg:hidden text-gray-400 hover:text-gray-200">
          <Menu className="w-5 h-5" />
        </button>
        <h2 className="text-gray-100 font-semibold text-lg">{title}</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs">
          <Server className="w-3.5 h-3.5 text-gray-500" />
          <span className={`w-1.5 h-1.5 rounded-full ${trackerConnected ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-gray-400 hidden sm:inline">Tracker</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <HardDrive className="w-3.5 h-3.5 text-gray-500" />
          <span className={`w-1.5 h-1.5 rounded-full ${peerConnected ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-gray-400 hidden sm:inline">{peerStatus?.peer_id || 'Peer'}</span>
        </div>
      </div>
    </header>
  );
}
