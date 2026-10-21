import type { TransferStatus } from '../../types/transfer';

interface Props {
  percent: number;
  status: TransferStatus;
  size?: 'sm' | 'md';
}

const barGradients: Record<string, string> = {
  downloading: 'bg-gradient-to-r from-cyan-500 to-blue-500 shadow-[0_0_12px_rgba(6,182,212,0.5)]',
  connecting: 'bg-gradient-to-r from-cyan-400 to-indigo-400',
  pending: 'bg-slate-500',
  verifying: 'bg-gradient-to-r from-amber-500 to-orange-500 shadow-[0_0_12px_rgba(245,158,11,0.5)]',
  completed: 'bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_12px_rgba(16,185,129,0.5)]',
  failed: 'bg-gradient-to-r from-rose-500 to-red-600 shadow-[0_0_12px_rgba(244,63,94,0.5)]',
  cancelled: 'bg-slate-600',
};

export function ProgressBar({ percent, status, size = 'sm' }: Props) {
  const h = size === 'sm' ? 'h-1.5' : 'h-2.5';
  const gradient = barGradients[status] || barGradients.downloading;
  const clamped = Math.min(100, Math.max(0, percent));

  return (
    <div className="flex items-center gap-2.5 w-full">
      <div className={`flex-1 bg-slate-950/70 border border-white/[0.08] rounded-full ${h} overflow-hidden p-[1px]`}>
        <div
          className={`${h} ${gradient} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {size === 'md' && (
        <span className="text-[11px] font-mono font-medium text-slate-300 w-11 text-right">
          {clamped.toFixed(0)}%
        </span>
      )}
    </div>
  );
}
