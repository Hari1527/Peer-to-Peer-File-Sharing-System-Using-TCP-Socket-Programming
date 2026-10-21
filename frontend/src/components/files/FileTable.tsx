import { FileText, FolderOpen, Eye, Download, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { EmptyState } from '../ui/EmptyState';
import { formatBytes, formatRelativeTime, truncateHash } from '../../utils/format';
import type { SharedFileInfo } from '../../types/file';

interface Props {
  files: SharedFileInfo[];
  loading: boolean;
  onViewPeers: (file: SharedFileInfo) => void;
  onDownload: (file: SharedFileInfo) => void;
  emptyMessage?: string;
}

export function FileTable({ files, loading, onViewPeers, onDownload, emptyMessage }: Props) {
  const [copied, setCopied] = useState<string | null>(null);

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopied(hash);
    setTimeout(() => setCopied(null), 2000);
  };

  if (loading) return <LoadingSkeleton variant="table" count={5} />;
  if (files.length === 0)
    return <EmptyState icon={<FolderOpen className="w-12 h-12" />} title="No files found" description={emptyMessage || 'Share files from a peer agent to see them here.'} />;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-xs uppercase text-gray-500 font-medium">
            <th className="text-left py-3 px-3">Filename</th>
            <th className="text-left py-3 px-3">Size</th>
            <th className="text-left py-3 px-3">SHA-256</th>
            <th className="text-left py-3 px-3">Peer</th>
            <th className="text-left py-3 px-3">Shared</th>
            <th className="text-right py-3 px-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {files.map(f => (
            <tr key={`${f.file_id}-${f.peer_id}`} className="border-b border-[#2a2d3a] hover:bg-[#1e2130] transition-colors">
              <td className="py-3 px-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-gray-500 shrink-0" />
                  <span className="text-sm text-gray-100 font-medium truncate max-w-48">{f.filename}</span>
                </div>
              </td>
              <td className="py-3 px-3 text-sm text-gray-400 whitespace-nowrap">{formatBytes(f.size)}</td>
              <td className="py-3 px-3">
                <button onClick={() => copyHash(f.checksum)} className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 font-mono transition-colors">
                  {truncateHash(f.checksum)}
                  {copied === f.checksum ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                </button>
              </td>
              <td className="py-3 px-3">
                <span className="text-xs bg-[#2a2d3a] text-gray-300 px-2 py-0.5 rounded font-mono">{f.peer_id.slice(0, 8)}</span>
              </td>
              <td className="py-3 px-3 text-sm text-gray-500 whitespace-nowrap">{formatRelativeTime(f.shared_at)}</td>
              <td className="py-3 px-3">
                <div className="flex items-center justify-end gap-1">
                  <button onClick={() => onViewPeers(f)} className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-[#2a2d3a] rounded transition-colors" title="View peers">
                    <Eye className="w-4 h-4" />
                  </button>
                  <button onClick={() => onDownload(f)} className="p-1.5 text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 rounded transition-colors" title="Download">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
