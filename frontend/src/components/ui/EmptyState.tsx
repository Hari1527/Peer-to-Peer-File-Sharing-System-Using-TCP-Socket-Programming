import type { ReactNode } from 'react';

interface Props {
  icon: ReactNode;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-16 h-16 rounded-2xl glass-card flex items-center justify-center text-slate-400 mb-4 border border-white/10 shadow-lg shadow-black/20">
        {icon}
      </div>
      <h3 className="text-white font-medium text-base mb-1.5">{title}</h3>
      <p className="text-slate-400 text-xs max-w-sm mb-5 leading-relaxed">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="glass-button-primary px-4 py-2 text-white text-xs font-medium rounded-xl shadow-md transition-transform"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
