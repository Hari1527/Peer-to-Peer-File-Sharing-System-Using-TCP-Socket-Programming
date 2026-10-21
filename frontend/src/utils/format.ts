export function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

export function formatSpeed(bytesPerSecond: number): string {
  if (bytesPerSecond <= 0) return '0 B/s';
  return `${formatBytes(bytesPerSecond)}/s`;
}

export function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true,
    });
  } catch { return iso; }
}

export function formatRelativeTime(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const secs = Math.floor(diff / 1000);
    if (secs < 5) return 'just now';
    if (secs < 60) return `${secs}s ago`;
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  } catch { return iso; }
}

export function truncateHash(hash: string, length = 6): string {
  if (!hash || hash.length <= length * 2 + 3) return hash;
  return `${hash.slice(0, length)}...${hash.slice(-length)}`;
}

export function formatDuration(startIso: string, endIso?: string | null): string {
  try {
    const start = new Date(startIso).getTime();
    const end = endIso ? new Date(endIso).getTime() : Date.now();
    const secs = Math.floor((end - start) / 1000);
    if (secs < 60) return `${secs}s`;
    const mins = Math.floor(secs / 60);
    const remSecs = secs % 60;
    if (mins < 60) return `${mins}m ${remSecs}s`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}h ${mins % 60}m`;
  } catch { return '-'; }
}

export function formatPercentage(value: number): string {
  return `${Math.min(100, Math.max(0, value)).toFixed(1)}%`;
}

export function getStatusColor(status: string): string {
  const s = status.toLowerCase();
  if (s === 'online' || s === 'completed') return 'text-emerald-400';
  if (s === 'offline' || s === 'failed') return 'text-red-400';
  if (s === 'downloading' || s === 'connecting' || s === 'pending') return 'text-blue-400';
  if (s === 'verifying') return 'text-amber-400';
  if (s === 'cancelled') return 'text-gray-400';
  return 'text-gray-400';
}

export function getStatusBgColor(status: string): string {
  const s = status.toLowerCase();
  if (s === 'online' || s === 'completed') return 'bg-emerald-500/10';
  if (s === 'offline' || s === 'failed') return 'bg-red-500/10';
  if (s === 'downloading' || s === 'connecting' || s === 'pending') return 'bg-blue-500/10';
  if (s === 'verifying') return 'bg-amber-500/10';
  if (s === 'cancelled') return 'bg-gray-500/10';
  return 'bg-gray-500/10';
}
