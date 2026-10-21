import { useEffect } from 'react';
import { X } from 'lucide-react';
import type { ReactNode } from 'react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg';
}

const widths = { sm: 'max-w-md', md: 'max-w-lg', lg: 'max-w-2xl' };

export function Modal({ isOpen, onClose, title, children, size = 'md' }: Props) {
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      {/* Blurred Backdrop */}
      <div className="fixed inset-0 bg-black/70 backdrop-blur-md transition-opacity" />

      {/* Glass Modal Box */}
      <div
        className={`relative glass-panel rounded-2xl border border-white/15 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.7)] w-full ${widths[size]} animate-fade-in z-10 overflow-hidden`}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4.5 border-b border-white/[0.08] bg-white/[0.02]">
          <h2 className="text-white font-semibold text-sm sm:text-base tracking-tight">{title}</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/[0.08] transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-4.5 h-4.5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}
