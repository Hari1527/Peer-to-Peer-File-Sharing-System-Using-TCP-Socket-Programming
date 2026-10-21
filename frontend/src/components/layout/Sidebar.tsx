import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FolderOpen, Users, ArrowUpDown,
  Activity, Settings, Wifi, WifiOff, ChevronLeft, ChevronRight, Share2
} from 'lucide-react';

interface Props {
  trackerConnected: boolean;
  peerConnected: boolean;
  mobileOpen: boolean;
  collapsed: boolean;
  onToggleCollapse: () => void;
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

export function Sidebar({ trackerConnected, peerConnected, mobileOpen, collapsed, onToggleCollapse, onClose }: Props) {
  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Glass Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full z-40 flex flex-col transition-all duration-300 ${
          collapsed ? 'w-20' : 'w-64'
        } glass-panel border-r border-white/10 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Header / Brand */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20 border border-white/20">
              <Share2 className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <div className="min-w-0 transition-opacity duration-200">
                <h1 className="text-sm font-semibold tracking-wide text-white flex items-center gap-1.5">
                  P2P<span className="text-cyan-400 font-light">Mesh</span>
                </h1>
                <p className="text-[10px] text-slate-400 font-mono tracking-wider">SOCKET PROTOCOL</p>
              </div>
            )}
          </div>

          <button
            onClick={onToggleCollapse}
            className="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/10 text-cyan-300 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent'
                } ${collapsed ? 'justify-center px-0' : ''}`
              }
              title={collapsed ? label : undefined}
            >
              <Icon className="w-4.5 h-4.5 shrink-0 transition-transform group-hover:scale-110" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Connection Status Footer */}
        <div className="p-3 border-t border-white/[0.08] space-y-2">
          {!collapsed ? (
            <div className="bg-slate-900/50 rounded-xl p-2.5 border border-white/[0.06] space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className={`w-2 h-2 rounded-full ${trackerConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-400 shadow-[0_0_8px_#f87171]'}`} />
                  Tracker
                </span>
                <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${trackerConnected ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'}`}>
                  {trackerConnected ? 'CONNECTED' : 'OFFLINE'}
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className={`w-2 h-2 rounded-full ${peerConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-400 shadow-[0_0_8px_#f87171]'}`} />
                  Local Node
                </span>
                <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${peerConnected ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'}`}>
                  {peerConnected ? 'ONLINE' : 'DISCONNECTED'}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-1">
              <div className={`w-2.5 h-2.5 rounded-full ${trackerConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-400'}`} title={`Tracker: ${trackerConnected ? 'Connected' : 'Offline'}`} />
              <div className={`w-2.5 h-2.5 rounded-full ${peerConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-400'}`} title={`Peer: ${peerConnected ? 'Online' : 'Disconnected'}`} />
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
