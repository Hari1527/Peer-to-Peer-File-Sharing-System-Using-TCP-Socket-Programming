import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Something went wrong', message, onRetry }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
      <h3 className="text-gray-300 font-medium text-lg mb-1">{title}</h3>
      <p className="text-gray-500 text-sm max-w-sm mb-4">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="inline-flex items-center gap-2 px-4 py-2 bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 text-sm rounded-lg transition-colors">
          <RefreshCw className="w-4 h-4" /> Retry
        </button>
      )}
    </div>
  );
}
