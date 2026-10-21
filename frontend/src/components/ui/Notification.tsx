import { useEffect } from 'react';
import { X, CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import type { AppNotification } from '../../types/events';

interface Props {
  notifications: AppNotification[];
  onDismiss: (id: string) => void;
}

const icons = {
  success: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  error: <AlertCircle className="w-4 h-4 text-red-400" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  info: <Info className="w-4 h-4 text-blue-400" />,
};

const borders = {
  success: 'border-emerald-500/30',
  error: 'border-red-500/30',
  warning: 'border-amber-500/30',
  info: 'border-blue-500/30',
};

export function Notification({ notifications, onDismiss }: Props) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
      {notifications.slice(0, 5).map(n => (
        <NotificationItem key={n.id} notification={n} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function NotificationItem({ notification: n, onDismiss }: { notification: AppNotification; onDismiss: (id: string) => void }) {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(n.id), 5000);
    return () => clearTimeout(t);
  }, [n.id, onDismiss]);

  return (
    <div className={`flex items-start gap-3 bg-[#1a1d28] border ${borders[n.type]} rounded-lg p-3 shadow-lg shadow-black/30 animate-fade-in`}>
      <span className="mt-0.5">{icons[n.type]}</span>
      <p className="flex-1 text-sm text-gray-200">{n.message}</p>
      <button onClick={() => onDismiss(n.id)} className="text-gray-500 hover:text-gray-300">
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
