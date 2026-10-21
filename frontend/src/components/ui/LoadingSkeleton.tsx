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
          <div key={i} className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5 animate-pulse">
            <div className="h-4 w-20 bg-[#2a2d3a] rounded mb-3" />
            <div className="h-8 w-16 bg-[#2a2d3a] rounded" />
          </div>
        ))}
      </div>
    );

  if (variant === 'table')
    return (
      <div className="space-y-3">
        {items.map((_, i) => (
          <div key={i} className="flex gap-4 animate-pulse">
            <div className="h-4 bg-[#2a2d3a] rounded flex-1" />
            <div className="h-4 bg-[#2a2d3a] rounded w-20" />
            <div className="h-4 bg-[#2a2d3a] rounded w-24" />
          </div>
        ))}
      </div>
    );

  if (variant === 'text')
    return (
      <div className="space-y-2">
        {items.map((_, i) => (
          <div key={i} className="h-4 bg-[#2a2d3a] rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
        ))}
      </div>
    );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((_, i) => (
        <div key={i} className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5 animate-pulse">
          <div className="h-4 w-24 bg-[#2a2d3a] rounded mb-4" />
          <div className="h-3 w-full bg-[#2a2d3a] rounded mb-2" />
          <div className="h-3 w-3/4 bg-[#2a2d3a] rounded" />
        </div>
      ))}
    </div>
  );
}
