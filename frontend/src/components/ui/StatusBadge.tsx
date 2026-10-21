import { getStatusColor, getStatusBgColor } from '../../utils/format';

interface Props {
  status: string;
  size?: 'sm' | 'md';
}

const dotColor: Record<string, string> = {
  online: 'bg-emerald-400', completed: 'bg-emerald-400',
  offline: 'bg-red-400', failed: 'bg-red-400',
  downloading: 'bg-blue-400', connecting: 'bg-blue-400', pending: 'bg-blue-400',
  verifying: 'bg-amber-400',
  cancelled: 'bg-gray-400',
};

export function StatusBadge({ status, size = 'sm' }: Props) {
  const s = status.toLowerCase();
  const textCls = getStatusColor(s);
  const bgCls = getStatusBgColor(s);
  const dot = dotColor[s] || 'bg-gray-400';
  const sz = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${sz} ${textCls} ${bgCls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot} ${s === 'downloading' || s === 'connecting' ? 'animate-pulse-subtle' : ''}`} />
      {s.charAt(0).toUpperCase() + s.slice(1)}
    </span>
  );
}
