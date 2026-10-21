import { useAppContext } from '../context/AppContext';
import { ActivityFeed } from '../components/activity/ActivityFeed';
import { Activity, Radio } from 'lucide-react';

export default function ActivityPage() {
  const { state, clearActivityLogs } = useAppContext();

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between pb-1">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
          </span>
          <p className="text-xs text-slate-400 font-mono">
            WebSocket feed connected to {state.trackerUrl} & {state.peerUrl}
          </p>
        </div>
      </div>

      <ActivityFeed logs={state.activityLogs} loading={false} onClear={clearActivityLogs} />
    </div>
  );
}
