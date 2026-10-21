import type { ReactNode } from 'react';

interface Props {
  icon: ReactNode;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-gray-600 mb-4">{icon}</div>
      <h3 className="text-gray-300 font-medium text-lg mb-1">{title}</h3>
      <p className="text-gray-500 text-sm max-w-sm mb-4">{description}</p>
      {action && (
        <button onClick={action.onClick} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors">
          {action.label}
        </button>
      )}
    </div>
  );
}
