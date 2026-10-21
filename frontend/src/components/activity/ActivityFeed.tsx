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
  info: <Info className="w-3.5 h-3.5 text-blue-400" />,
  success: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
  warning: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />,
  error: <AlertCircle className="w-3.5 h-3.5 text-red-400" />,
};

const catColors: Record<string, string> = {
  peer: 'bg-blue-500/10 text-blue-400',
  file: 'bg-emerald-500/10 text-emerald-400',
  transfer: 'bg-amber-500/10 text-amber-400',
  system: 'bg-gray-500/10 text-gray-400',
};

const categories = ['all', 'peer', 'file', 'transfer'] as const;

export function ActivityFeed({ logs, loading, onClear }: Props) {
  const [catFilter, setCatFilter] = useState<string>('all');
  const filtered = catFilter === 'all' ? logs : logs.filter(l => l.category === catFilter);

  return (
    <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a]">
      <div className="flex items-center justify-between px-5 py-3 border-b border-[#2a2d3a]">
        <div className="flex items-center gap-2">
          {categories.map(c => (
            <button key={c} onClick={() => setCatFilter(c)}
              className={`px-2.5 py-1 text-xs rounded-lg transition-colors ${catFilter === c ? 'bg-blue-500/10 text-blue-400' : 'text-gray-500 hover:text-gray-300'}`}>
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </button>
          ))}
        </div>
        {onClear && logs.length > 0 && (
          <button onClick={onClear} className="text-gray-500 hover:text-gray-300 p-1 transition-colors" title="Clear logs">
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="max-h-[600px] overflow-y-auto">
        {loading ? (
          <div className="p-4 space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-10 bg-[#2a2d3a] rounded animate-pulse" />)}</div>
        ) : filtered.length === 0 ? (
          <EmptyState icon={<Activity className="w-10 h-10" />} title="No activity" description="Events from WebSocket connections will appear here." />
        ) : (
          <div className="divide-y divide-[#2a2d3a]">
            {filtered.map(log => (
              <div key={log.id} className="flex items-start gap-3 px-5 py-3 animate-fade-in hover:bg-[#1e2130] transition-colors">
                <span className="mt-0.5 shrink-0">{sevIcons[log.severity]}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200">{log.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${catColors[log.category]}`}>{log.category}</span>
                    {log.peer_id && <span className="text-xs text-gray-500 font-mono">{log.peer_id.slice(0, 8)}</span>}
                  </div>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap shrink-0">{formatTimestamp(log.timestamp)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
