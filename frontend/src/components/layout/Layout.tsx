import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { Notification } from '../ui/Notification';
import type { PeerStatus } from '../../types/peer';
import type { AppNotification } from '../../types/events';

interface Props {
  trackerConnected: boolean;
  peerConnected: boolean;
  peerStatus: PeerStatus | null;
  notifications: AppNotification[];
  onDismissNotification: (id: string) => void;
}

const pageTitles: Record<string, string> = {
  '/': 'Overview',
  '/files': 'File Explorer',
  '/peers': 'Peers',
  '/transfers': 'Transfers',
  '/activity': 'Activity',
  '/settings': 'Settings',
};

export default function Layout({ trackerConnected, peerConnected, peerStatus, notifications, onDismissNotification }: Props) {
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const title = pageTitles[pathname] || 'P2P File Sharing';

  return (
    <div className="min-h-screen bg-[#0f1117]">
      <Sidebar trackerConnected={trackerConnected} peerConnected={peerConnected} mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <div className="lg:ml-64 flex flex-col min-h-screen">
        <TopBar title={title} trackerConnected={trackerConnected} peerConnected={peerConnected} peerStatus={peerStatus} onMenuToggle={() => setMobileOpen(v => !v)} />
        <main className="flex-1 p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
      <Notification notifications={notifications} onDismiss={onDismissNotification} />
    </div>
  );
}
