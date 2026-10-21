import type { TransferStatus } from '../../types/transfer';

interface Props {
  percent: number;
  status: TransferStatus;
  size?: 'sm' | 'md';
}

const barColors: Record<string, string> = {
  downloading: 'bg-blue-500',
  connecting: 'bg-blue-400',
  pending: 'bg-gray-500',
  verifying: 'bg-amber-500',
  completed: 'bg-emerald-500',
  failed: 'bg-red-500',
  cancelled: 'bg-gray-500',
};

export function ProgressBar({ percent, status, size = 'sm' }: Props) {
  const h = size === 'sm' ? 'h-1.5' : 'h-2';
  const color = barColors[status] || 'bg-blue-500';
  const clamped = Math.min(100, Math.max(0, percent));

  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 bg-[#2a2d3a] rounded-full ${h} overflow-hidden`}>
        <div className={`${h} ${color} rounded-full transition-all duration-300`} style={{ width: `${clamped}%` }} />
      </div>
      {size === 'md' && <span className="text-xs text-gray-400 w-10 text-right">{clamped.toFixed(0)}%</span>}
    </div>
  );
}
