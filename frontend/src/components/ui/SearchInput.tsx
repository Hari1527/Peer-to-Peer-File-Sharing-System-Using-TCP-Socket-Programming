import { Search, X } from 'lucide-react';

interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onSearch?: () => void;
}

export function SearchInput({ value, onChange, placeholder = 'Search files...', onSearch }: Props) {
  return (
    <div className="relative w-full">
      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && onSearch?.()}
        placeholder={placeholder}
        className="glass-input w-full rounded-xl pl-10 pr-9 py-2 text-xs text-white placeholder-slate-400 focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-all"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors p-0.5 rounded-md hover:bg-white/10"
          aria-label="Clear search"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
