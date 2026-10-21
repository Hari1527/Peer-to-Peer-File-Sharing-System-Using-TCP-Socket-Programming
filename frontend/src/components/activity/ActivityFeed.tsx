import { useState } from 'react';
import { Activity, Trash2, CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatTimestamp } from '../../utils/format';
import type { ActivityLogEntry } from '../../types/events';

interface Props {
  logs: ActivityLogEntry[];
  loading: boolean;
  onClear?: () => void;
}

const sevIcons = {
  info: <Info className="w-4 h-4 text-cyan-400" />,
  success: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  error: <AlertCircle className="w-4 h-4 text-rose-400" />,
};

const catColors: Record<string, string> = {
  peer: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20',
  file: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  transfer: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  system: 'bg-slate-500/10 text-slate-300 border-slate-500/20',
};

const categories = ['all', 'peer', 'file', 'transfer'] as const;

export function ActivityFeed({ logs, loading, onClear }: Props) {
  const [catFilter, setCatFilter] = useState<string>('all');
  const filtered = catFilter === 'all' ? logs : logs.filter(l => l.category === catFilter);

  return (
    <div className="glass-panel rounded-2xl border border-white/[0.08] shadow-2xl overflow-hidden">
      {/* Feed Filter Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.08] bg-white/[0.02]">
        <div className="flex items-center gap-1.5">
          {categories.map(c => (
            <button
              key={c}
              onClick={() => setCatFilter(c)}
              className={`px-3 py-1.5 text-xs rounded-xl font-medium transition-all ${
                catFilter === c
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.15)]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.05] border border-transparent'
              }`}
            >
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </button>
          ))}
        </div>
        {onClear && logs.length > 0 && (
          <button
            onClick={onClear}
            className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all flex items-center gap-1 text-xs"
            title="Clear telemetry logs"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </button>
        )}
      </div>

      {/* Feed Content */}
      <div className="max-h-[620px] overflow-y-auto">
        {loading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 bg-white/[0.04] rounded-xl animate-shimmer" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Activity className="w-9 h-9" />}
            title="Telemetry idle"
            description="Real-time events broadcast over WebSockets (/ws/events) will stream here."
          />
        ) : (
          <div className="divide-y divide-white/[0.04]">
            {filtered.map(log => (
              <div
                key={log.id}
                className="flex items-start gap-3.5 px-5 py-3.5 animate-fade-in hover:bg-white/[0.02] transition-colors"
              >
                <span className="mt-0.5 shrink-0">{sevIcons[log.severity]}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs sm:text-sm text-slate-100 font-medium leading-relaxed">
                    {log.message}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-md font-mono border ${
                        catColors[log.category] || catColors.system
                      }`}
                    >
                      {log.category.toUpperCase()}
                    </span>
                    {log.peer_id && (
                      <span className="text-[10px] text-slate-400 font-mono bg-white/[0.04] px-1.5 py-0.5 rounded border border-white/[0.06]">
                        {log.peer_id.slice(0, 8)}
                      </span>
                    )}
                  </div>
                </div>
                <span className="text-[10px] text-slate-500 font-mono whitespace-nowrap shrink-0">
                  {formatTimestamp(log.timestamp)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
