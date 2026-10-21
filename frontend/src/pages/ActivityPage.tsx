import { useAppContext } from '../context/AppContext';
import { ActivityFeed } from '../components/activity/ActivityFeed';

export default function ActivityPage() {
  const { state, clearActivityLogs } = useAppContext();

  return (
    <div className="animate-fade-in">
      <ActivityFeed logs={state.activityLogs} loading={false} onClear={clearActivityLogs} />
    </div>
  );
}
