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

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Overview', subtitle: 'Network telemetry & real-time node health' },
  '/files': { title: 'File Explorer', subtitle: 'Browse, inspect, and initiate peer transfers' },
  '/peers': { title: 'Peers Discovery', subtitle: 'Connected nodes & routing topology' },
  '/transfers': { title: 'Transfer Center', subtitle: 'Active downloads, progress & audit history' },
  '/activity': { title: 'Activity Telemetry', subtitle: 'Live event stream from WebSocket feeds' },
  '/settings': { title: 'System Settings', subtitle: 'Tracker endpoints, node config & diagnostics' },
};

export default function Layout({ trackerConnected, peerConnected, peerStatus, notifications, onDismissNotification }: Props) {
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const current = pageTitles[pathname] || { title: 'P2P Network', subtitle: 'File Sharing Dashboard' };

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 relative overflow-x-hidden font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Ambient background glows for glassmorphism refraction */}
      <div className="fixed -top-40 -left-40 w-[30rem] h-[30rem] bg-indigo-600/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="fixed top-1/3 -right-40 w-[32rem] h-[32rem] bg-cyan-600/15 rounded-full blur-[150px] pointer-events-none" />
      <div className="fixed -bottom-40 left-1/3 w-[36rem] h-[36rem] bg-blue-600/10 rounded-full blur-[160px] pointer-events-none" />

      {/* Main Glass Shell */}
      <div className="relative z-10 flex min-h-screen">
        <Sidebar
          trackerConnected={trackerConnected}
          peerConnected={peerConnected}
          mobileOpen={mobileOpen}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(c => !c)}
          onClose={() => setMobileOpen(false)}
        />

        <div className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-20' : 'lg:ml-64'}`}>
          <TopBar
            title={current.title}
            subtitle={current.subtitle}
            trackerConnected={trackerConnected}
            peerConnected={peerConnected}
            peerStatus={peerStatus}
            onMenuToggle={() => setMobileOpen(v => !v)}
          />

          <main className="flex-1 p-4 lg:p-7 max-w-7xl w-full mx-auto">
            <Outlet />
          </main>
        </div>
      </div>

      <Notification notifications={notifications} onDismiss={onDismissNotification} />
    </div>
  );
}
