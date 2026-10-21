import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Connection issue detected', message, onRetry }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-4 shadow-[0_0_25px_rgba(244,63,94,0.15)]">
        <AlertTriangle className="w-8 h-8" />
      </div>
      <h3 className="text-white font-medium text-base mb-1.5">{title}</h3>
      <p className="text-slate-400 text-xs max-w-sm mb-5 leading-relaxed font-mono">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="glass-button inline-flex items-center gap-2 px-4 py-2 text-slate-200 text-xs font-medium rounded-xl hover:text-white transition-all shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Try Again
        </button>
      )}
    </div>
  );
}
