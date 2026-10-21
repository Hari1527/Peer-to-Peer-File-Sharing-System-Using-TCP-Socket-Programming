interface Props {
  status: string;
  size?: 'sm' | 'md';
}

const statusConfig: Record<string, { text: string; bg: string; dot: string; glow: string }> = {
  online: {
    text: 'text-emerald-300',
    bg: 'bg-emerald-500/10 border-emerald-500/20',
    dot: 'bg-emerald-400',
    glow: 'shadow-[0_0_8px_rgba(52,211,153,0.5)]',
  },
  completed: {
    text: 'text-emerald-300',
    bg: 'bg-emerald-500/10 border-emerald-500/20',
    dot: 'bg-emerald-400',
    glow: 'shadow-[0_0_8px_rgba(52,211,153,0.5)]',
  },
  downloading: {
    text: 'text-cyan-300',
    bg: 'bg-cyan-500/10 border-cyan-500/20',
    dot: 'bg-cyan-400 animate-pulse',
    glow: 'shadow-[0_0_8px_rgba(34,211,238,0.5)]',
  },
  connecting: {
    text: 'text-cyan-300',
    bg: 'bg-cyan-500/10 border-cyan-500/20',
    dot: 'bg-cyan-400 animate-pulse',
    glow: 'shadow-[0_0_8px_rgba(34,211,238,0.5)]',
  },
  pending: {
    text: 'text-blue-300',
    bg: 'bg-blue-500/10 border-blue-500/20',
    dot: 'bg-blue-400',
    glow: 'shadow-[0_0_8px_rgba(96,165,250,0.5)]',
  },
  verifying: {
    text: 'text-amber-300',
    bg: 'bg-amber-500/10 border-amber-500/20',
    dot: 'bg-amber-400 animate-pulse',
    glow: 'shadow-[0_0_8px_rgba(251,191,36,0.5)]',
  },
  failed: {
    text: 'text-rose-300',
    bg: 'bg-rose-500/10 border-rose-500/20',
    dot: 'bg-rose-400',
    glow: 'shadow-[0_0_8px_rgba(251,113,133,0.5)]',
  },
  offline: {
    text: 'text-rose-300',
    bg: 'bg-rose-500/10 border-rose-500/20',
    dot: 'bg-rose-400',
    glow: 'shadow-[0_0_8px_rgba(251,113,133,0.5)]',
  },
  cancelled: {
    text: 'text-slate-400',
    bg: 'bg-slate-500/10 border-slate-500/20',
    dot: 'bg-slate-400',
    glow: '',
  },
};

export function StatusBadge({ status, size = 'sm' }: Props) {
  const s = status.toLowerCase();
  const cfg = statusConfig[s] || {
    text: 'text-slate-300',
    bg: 'bg-slate-500/10 border-slate-500/20',
    dot: 'bg-slate-400',
    glow: '',
  };

  const sz = size === 'sm' ? 'text-[11px] px-2.5 py-0.5' : 'text-xs px-3 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium tracking-wide border backdrop-blur-md ${sz} ${cfg.text} ${cfg.bg}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot} ${cfg.glow}`} />
      <span className="capitalize">{s}</span>
    </span>
  );
}
