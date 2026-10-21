import { useState } from 'react';
import {
  Save, CheckCircle2, Server, HardDrive, Info, RotateCcw,
  ShieldCheck, Cpu, Terminal, Radio, Network
} from 'lucide-react';
import { useAppContext, useTrackerApi, usePeerApi } from '../context/AppContext';

export default function SettingsPage() {
  const { state, setTrackerUrl, setPeerUrl, addNotification } = useAppContext();
  const trackerApi = useTrackerApi();
  const peerApi = usePeerApi();

  const [trackerInput, setTrackerInput] = useState(state.trackerUrl);
  const [peerInput, setPeerInput] = useState(state.peerUrl);
  const [saved, setSaved] = useState(false);
  const [testingTracker, setTestingTracker] = useState(false);
  const [testingPeer, setTestingPeer] = useState(false);

  const handleSave = () => {
    setTrackerUrl(trackerInput);
    setPeerUrl(peerInput);
    setSaved(true);
    addNotification('success', 'Endpoint configurations saved & applied');
    setTimeout(() => setSaved(false), 2000);
  };

  const testTracker = async () => {
    setTestingTracker(true);
    try {
      await trackerApi.getHealth();
      addNotification('success', 'Tracker server is active & responding');
    } catch {
      addNotification('error', 'Unable to reach tracker server at this URL');
    }
    setTestingTracker(false);
  };

  const testPeer = async () => {
    setTestingPeer(true);
    try {
      await peerApi.getStatus();
      addNotification('success', 'Local peer agent responded with valid status');
    } catch {
      addNotification('error', 'Unable to reach peer agent at this URL');
    }
    setTestingPeer(false);
  };

  const handleReset = () => {
    setTrackerInput('http://localhost:8000');
    setPeerInput('http://localhost:8001');
  };

  return (
    <div className="space-y-6 max-w-3xl animate-fade-in pb-10">
      {/* Connection Endpoints Config */}
      <div className="glass-panel rounded-2xl border border-white/[0.08] p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-white font-semibold text-sm">Target Endpoints</h3>
            <p className="text-[11px] text-slate-400">
              Configure tracker registry and local peer REST control ports
            </p>
          </div>
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-md border border-cyan-500/20">
            DYNAMIC SWITCHER
          </span>
        </div>

        <div className="space-y-4.5">
          {/* Tracker URL */}
          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-300 mb-2">
              <Server className="w-3.5 h-3.5 text-cyan-400" />
              <span>Tracker Server REST API</span>
              <span className="ml-auto flex items-center gap-1.5 text-[10px] font-mono">
                <span
                  className={`w-2 h-2 rounded-full ${
                    state.trackerConnected
                      ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                      : 'bg-rose-400'
                  }`}
                />
                <span className={state.trackerConnected ? 'text-emerald-400' : 'text-rose-400'}>
                  {state.trackerConnected ? 'REACHABLE' : 'UNREACHABLE'}
                </span>
              </span>
            </label>
            <div className="flex gap-2">
              <input
                value={trackerInput}
                onChange={e => setTrackerInput(e.target.value)}
                placeholder="http://localhost:8000"
                className="glass-input flex-1 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-slate-500 outline-none focus:border-cyan-400/50"
              />
              <button
                onClick={testTracker}
                disabled={testingTracker}
                className="glass-button px-4 py-2 text-xs font-medium text-slate-300 hover:text-white rounded-xl transition-all disabled:opacity-50 whitespace-nowrap shadow-sm"
              >
                {testingTracker ? 'Pinging...' : 'Test Connection'}
              </button>
            </div>
          </div>

          {/* Peer Agent URL */}
          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-300 mb-2">
              <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
              <span>Target Peer Agent API (Local Node)</span>
              <span className="ml-auto flex items-center gap-1.5 text-[10px] font-mono">
                <span
                  className={`w-2 h-2 rounded-full ${
                    state.peerConnected
                      ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                      : 'bg-rose-400'
                  }`}
                />
                <span className={state.peerConnected ? 'text-emerald-400' : 'text-rose-400'}>
                  {state.peerConnected ? 'ONLINE' : 'DISCONNECTED'}
                </span>
              </span>
            </label>
            <div className="flex gap-2">
              <input
                value={peerInput}
                onChange={e => setPeerInput(e.target.value)}
                placeholder="http://localhost:8001"
                className="glass-input flex-1 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-slate-500 outline-none focus:border-cyan-400/50"
              />
              <button
                onClick={testPeer}
                disabled={testingPeer}
                className="glass-button px-4 py-2 text-xs font-medium text-slate-300 hover:text-white rounded-xl transition-all disabled:opacity-50 whitespace-nowrap shadow-sm"
              >
                {testingPeer ? 'Pinging...' : 'Test Connection'}
              </button>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 font-mono">
              💡 Switch between <span className="text-slate-400">http://localhost:8001</span> (Peer 1) and <span className="text-slate-400">http://localhost:8002</span> (Peer 2).
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 pt-3 border-t border-white/[0.08]">
            <button
              onClick={handleSave}
              className="glass-button-primary inline-flex items-center gap-2 px-5 py-2 text-xs font-medium text-white rounded-xl shadow-md transition-all hover:scale-[1.02]"
            >
              {saved ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
              <span>{saved ? 'Saved & Applied' : 'Save Configurations'}</span>
            </button>
            <button
              onClick={handleReset}
              className="glass-button inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-400 hover:text-white rounded-xl transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reset Defaults
            </button>
          </div>
        </div>
      </div>

      {/* Active Peer Diagnostics Card */}
      {state.peerStatus && (
        <div className="glass-panel rounded-2xl border border-white/[0.08] p-6 shadow-2xl">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <h3 className="text-white font-semibold text-sm">Active Node Telemetry</h3>
          </div>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            {[
              ['Identifier (Peer ID)', state.peerStatus.peer_id],
              ['Status', state.peerStatus.status.toUpperCase()],
              ['TCP Transfer Socket Port', state.peerStatus.tcp_port],
              ['REST Control Port', state.peerStatus.api_port],
              ['Shared Directory', state.peerStatus.shared_dir],
              ['Downloads Target Directory', state.peerStatus.download_dir],
              ['Files Indexed & Published', state.peerStatus.files_shared],
              ['Concurrent Socket Transfers', state.peerStatus.active_transfers],
            ].map(([label, value]) => (
              <div
                key={String(label)}
                className="glass-card p-3 rounded-xl border border-white/[0.05]"
              >
                <dt className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold">
                  {String(label)}
                </dt>
                <dd className="text-slate-100 font-mono text-xs mt-1 truncate font-medium">
                  {String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* Architectural Documentation Callout */}
      <div className="glass-panel rounded-2xl border border-white/[0.08] p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-3">
          <Info className="w-4 h-4 text-indigo-400" />
          <h3 className="text-white font-semibold text-sm">System Mechanics & TCP Architecture</h3>
        </div>
        <div className="text-xs text-slate-400 space-y-2 leading-relaxed">
          <p>
            • <strong className="text-slate-200">Zero-Relay Decentralization:</strong> The Tracker manages peer registrations, file metadata, and SHA-256 hashes. Actual binary file data is never transmitted through the tracker server.
          </p>
          <p>
            • <strong className="text-slate-200">Raw TCP Sockets:</strong> File downloads bypass HTTP and open direct TCP socket connections framed by a custom 8-byte binary header with 64KB chunk streaming.
          </p>
          <p>
            • <strong className="text-slate-200">Browser Security Sandbox:</strong> Web browsers cannot initiate raw TCP sockets directly; all transfers are commanded through the local Python peer agent's REST control API.
          </p>
        </div>
      </div>
    </div>
  );
}
