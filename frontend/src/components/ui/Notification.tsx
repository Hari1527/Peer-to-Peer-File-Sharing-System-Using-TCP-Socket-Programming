import { useEffect } from 'react';
import { X, CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import type { AppNotification } from '../../types/events';

interface Props {
  notifications: AppNotification[];
  onDismiss: (id: string) => void;
}

const toastConfigs = {
  success: {
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />,
    border: 'border-emerald-500/30',
    glow: 'shadow-[0_8px_30px_rgba(16,185,129,0.15)]',
    bg: 'bg-emerald-950/20',
  },
  error: {
    icon: <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />,
    border: 'border-rose-500/30',
    glow: 'shadow-[0_8px_30px_rgba(244,63,94,0.15)]',
    bg: 'bg-rose-950/20',
  },
  warning: {
    icon: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />,
    border: 'border-amber-500/30',
    glow: 'shadow-[0_8px_30px_rgba(245,158,11,0.15)]',
    bg: 'bg-amber-950/20',
  },
  info: {
    icon: <Info className="w-4 h-4 text-cyan-400 shrink-0" />,
    border: 'border-cyan-500/30',
    glow: 'shadow-[0_8px_30px_rgba(6,182,212,0.15)]',
    bg: 'bg-cyan-950/20',
  },
};

export function Notification({ notifications, onDismiss }: Props) {
  return (
    <div className="fixed top-5 right-5 z-50 flex flex-col gap-2.5 w-84 max-w-[calc(100vw-2.5rem)] pointer-events-none">
      {notifications.slice(0, 5).map(n => (
        <NotificationItem key={n.id} notification={n} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function NotificationItem({
  notification: n,
  onDismiss,
}: {
  notification: AppNotification;
  onDismiss: (id: string) => void;
}) {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(n.id), 5000);
    return () => clearTimeout(t);
  }, [n.id, onDismiss]);

  const cfg = toastConfigs[n.type] || toastConfigs.info;

  return (
    <div
      className={`pointer-events-auto flex items-start gap-3 glass-panel ${cfg.bg} border ${cfg.border} ${cfg.glow} rounded-xl p-3.5 animate-fade-in transition-all`}
    >
      <span className="mt-0.5">{cfg.icon}</span>
      <p className="flex-1 text-xs text-slate-200 leading-snug break-words">{n.message}</p>
      <button
        onClick={() => onDismiss(n.id)}
        className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-white/[0.08] transition-colors shrink-0"
        aria-label="Dismiss notification"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
