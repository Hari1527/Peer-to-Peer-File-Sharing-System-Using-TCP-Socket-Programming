import { Menu, Server, HardDrive, ShieldCheck, Activity } from 'lucide-react';
import type { PeerStatus } from '../../types/peer';

interface Props {
  title: string;
  subtitle?: string;
  trackerConnected: boolean;
  peerConnected: boolean;
  peerStatus: PeerStatus | null;
  onMenuToggle: () => void;
}

export function TopBar({ title, subtitle, trackerConnected, peerConnected, peerStatus, onMenuToggle }: Props) {
  return (
    <header className="h-16 sticky top-0 z-20 glass-panel border-b border-white/[0.08] flex items-center justify-between px-4 lg:px-8">
      {/* Title & Mobile Toggle */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-sm lg:text-base font-semibold text-white tracking-tight flex items-center gap-2">
            {title}
          </h2>
          {subtitle && (
            <p className="hidden sm:block text-[11px] text-slate-400 font-normal">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      {/* Network & Node Telemetry Pills */}
      <div className="flex items-center gap-2.5">
        {/* Tracker Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass-card text-xs border border-white/[0.06]">
          <Server className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="hidden md:inline text-slate-400 text-[11px]">Tracker</span>
          <span className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                trackerConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-400 shadow-[0_0_8px_#f87171]'
              }`}
            />
            <span className={`text-[10px] font-mono font-medium ${trackerConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
              {trackerConnected ? ':8000' : 'Offline'}
            </span>
          </span>
        </div>

        {/* Peer Node Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass-card text-xs border border-white/[0.06]">
          <HardDrive className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <div className="flex items-center gap-1.5 font-mono text-[11px]">
            <span className="text-slate-300 font-medium">
              {peerStatus ? peerStatus.peer_id : 'No Node'}
            </span>
            {peerStatus && (
              <span className="text-[10px] text-slate-500 hidden sm:inline">
                TCP:{peerStatus.tcp_port}
              </span>
            )}
            <span
              className={`w-2 h-2 rounded-full ${
                peerConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-400'
              }`}
            />
          </div>
        </div>
      </div>
    </header>
  );
}
