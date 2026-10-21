interface Props {
  variant?: 'card' | 'table' | 'text' | 'stat';
  count?: number;
}

export function LoadingSkeleton({ variant = 'card', count = 1 }: Props) {
  const items = Array.from({ length: count });

  if (variant === 'stat')
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {items.map((_, i) => (
          <div key={i} className="glass-card rounded-2xl p-5 border border-white/[0.07] overflow-hidden relative">
            <div className="h-4 w-24 rounded-lg bg-white/[0.06] animate-shimmer mb-4" />
            <div className="h-8 w-20 rounded-lg bg-white/[0.08] animate-shimmer" />
          </div>
        ))}
      </div>
    );

  if (variant === 'table')
    return (
      <div className="space-y-3 p-4">
        {items.map((_, i) => (
          <div key={i} className="flex items-center gap-4 py-2 border-b border-white/[0.04]">
            <div className="h-4 bg-white/[0.06] rounded-md flex-1 animate-shimmer" />
            <div className="h-4 bg-white/[0.05] rounded-md w-24 animate-shimmer" />
            <div className="h-4 bg-white/[0.05] rounded-md w-28 animate-shimmer" />
            <div className="h-8 bg-white/[0.06] rounded-lg w-20 animate-shimmer" />
          </div>
        ))}
      </div>
    );

  if (variant === 'text')
    return (
      <div className="space-y-2.5">
        {items.map((_, i) => (
          <div
            key={i}
            className="h-4 bg-white/[0.06] rounded-md animate-shimmer"
            style={{ width: `${60 + ((i * 13) % 35)}%` }}
          />
        ))}
      </div>
    );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((_, i) => (
        <div key={i} className="glass-card rounded-2xl p-5 border border-white/[0.07]">
          <div className="flex justify-between items-center mb-4">
            <div className="h-4 w-28 bg-white/[0.08] rounded-md animate-shimmer" />
            <div className="h-5 w-16 bg-white/[0.06] rounded-full animate-shimmer" />
          </div>
          <div className="space-y-2 mb-4">
            <div className="h-3 w-full bg-white/[0.05] rounded animate-shimmer" />
            <div className="h-3 w-3/4 bg-white/[0.05] rounded animate-shimmer" />
          </div>
          <div className="h-8 w-full bg-white/[0.06] rounded-xl animate-shimmer" />
        </div>
      ))}
    </div>
  );
}
