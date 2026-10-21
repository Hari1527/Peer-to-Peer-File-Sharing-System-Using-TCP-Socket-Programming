import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FolderOpen, Users, ArrowUpDown, Activity, Settings, Wifi, WifiOff } from 'lucide-react';

interface Props {
  trackerConnected: boolean;
  peerConnected: boolean;
  mobileOpen: boolean;
  onClose: () => void;
}

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Overview' },
  { to: '/files', icon: FolderOpen, label: 'File Explorer' },
  { to: '/peers', icon: Users, label: 'Peers' },
  { to: '/transfers', icon: ArrowUpDown, label: 'Transfers' },
  { to: '/activity', icon: Activity, label: 'Activity' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar({ trackerConnected, peerConnected, mobileOpen, onClose }: Props) {
  return (
    <>
      {mobileOpen && <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={onClose} />}
      <aside className={`fixed top-0 left-0 h-full w-64 bg-[#161922] border-r border-[#2a2d3a] z-40 flex flex-col transition-transform duration-200 lg:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="px-5 py-4 border-b border-[#2a2d3a]">
          <h1 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
            🔗 <span>P2P Share</span>
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">File Sharing Dashboard</p>
        </div>

        <nav className="flex-1 py-3 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 mx-2 px-4 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-500/10 text-blue-400 font-medium'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#1a1d28]'
                }`
              }
            >
              <Icon className="w-4.5 h-4.5" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-3 border-t border-[#2a2d3a] space-y-2">
          <div className="flex items-center gap-2 text-xs">
            {trackerConnected ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-red-400" />}
            <span className={trackerConnected ? 'text-gray-400' : 'text-red-400'}>Tracker</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            {peerConnected ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-red-400" />}
            <span className={peerConnected ? 'text-gray-400' : 'text-red-400'}>Peer Agent</span>
          </div>
        </div>
      </aside>
    </>
  );
}
