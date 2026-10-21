import { useState } from 'react';
import {
  FileText, FolderOpen, Eye, Download, Copy, Check,
  FileCode, FileArchive, Binary, FileImage, File
} from 'lucide-react';
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

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'js':
    case 'ts':
    case 'py':
    case 'json':
    case 'html':
      return <FileCode className="w-4 h-4 text-cyan-400" />;
    case 'zip':
    case 'tar':
    case 'gz':
    case 'rar':
      return <FileArchive className="w-4 h-4 text-amber-400" />;
    case 'bin':
    case 'dat':
    case 'exe':
      return <Binary className="w-4 h-4 text-indigo-400" />;
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'svg':
      return <FileImage className="w-4 h-4 text-emerald-400" />;
    case 'txt':
    case 'md':
      return <FileText className="w-4 h-4 text-blue-400" />;
    default:
      return <File className="w-4 h-4 text-slate-400" />;
  }
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
    return (
      <EmptyState
        icon={<FolderOpen className="w-10 h-10" />}
        title="No files indexed"
        description={emptyMessage || 'Start a peer agent or share files to view them here.'}
      />
    );

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-white/[0.08] text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-white/[0.01]">
            <th className="text-left py-3.5 px-4">Filename</th>
            <th className="text-left py-3.5 px-4">Size</th>
            <th className="text-left py-3.5 px-4">SHA-256 Checksum</th>
            <th className="text-left py-3.5 px-4">Origin Node</th>
            <th className="text-left py-3.5 px-4">Indexed</th>
            <th className="text-right py-3.5 px-4">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.04]">
          {files.map(f => (
            <tr
              key={`${f.file_id}-${f.peer_id}`}
              className="hover:bg-white/[0.03] transition-colors group"
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg glass-card flex items-center justify-center shrink-0 border border-white/[0.06]">
                    {getFileIcon(f.filename)}
                  </div>
                  <span className="text-xs font-medium text-slate-100 truncate max-w-xs group-hover:text-cyan-300 transition-colors">
                    {f.filename}
                  </span>
                </div>
              </td>
              <td className="py-3 px-4 text-xs text-slate-300 font-mono whitespace-nowrap">
                {formatBytes(f.size)}
              </td>
              <td className="py-3 px-4">
                <button
                  onClick={() => copyHash(f.checksum)}
                  className="flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-white font-mono glass-card px-2 py-1 rounded-md border border-white/[0.06] hover:border-cyan-500/30 transition-all"
                  title="Click to copy full hash"
                >
                  <span>{truncateHash(f.checksum)}</span>
                  {copied === f.checksum ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3 text-slate-500 group-hover:text-slate-300" />
                  )}
                </button>
              </td>
              <td className="py-3 px-4">
                <span className="text-[11px] bg-slate-800/60 text-slate-300 border border-white/[0.08] px-2 py-0.5 rounded font-mono">
                  {f.peer_id.slice(0, 8)}
                </span>
              </td>
              <td className="py-3 px-4 text-xs text-slate-400 font-mono whitespace-nowrap">
                {formatRelativeTime(f.shared_at)}
              </td>
              <td className="py-3 px-4 text-right">
                <div className="flex items-center justify-end gap-1.5">
                  <button
                    onClick={() => onViewPeers(f)}
                    className="p-1.5 text-slate-400 hover:text-white rounded-lg glass-card hover:bg-white/[0.08] border border-white/[0.05] transition-colors"
                    title="Inspect file & available peers"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDownload(f)}
                    className="p-1.5 text-cyan-400 hover:text-white rounded-lg bg-cyan-500/10 hover:bg-cyan-500/30 border border-cyan-500/30 transition-all shadow-sm"
                    title="Initiate direct TCP download"
                  >
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
