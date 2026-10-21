import { useState } from 'react';
import { Save, CheckCircle2, Wifi, WifiOff, Server, HardDrive, Info, RotateCcw } from 'lucide-react';
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
    addNotification('success', 'Settings saved');
    setTimeout(() => setSaved(false), 2000);
  };

  const testTracker = async () => {
    setTestingTracker(true);
    try {
      await trackerApi.getHealth();
      addNotification('success', 'Tracker is reachable');
    } catch { addNotification('error', 'Cannot reach tracker'); }
    setTestingTracker(false);
  };

  const testPeer = async () => {
    setTestingPeer(true);
    try {
      await peerApi.getStatus();
      addNotification('success', 'Peer agent is reachable');
    } catch { addNotification('error', 'Cannot reach peer agent'); }
    setTestingPeer(false);
  };

  const handleReset = () => {
    setTrackerInput('http://localhost:8000');
    setPeerInput('http://localhost:8001');
  };

  return (
    <div className="space-y-6 max-w-2xl animate-fade-in">
      {/* Connection Settings */}
      <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5">
        <h3 className="text-gray-100 font-semibold mb-4">Connection Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="flex items-center gap-2 text-sm text-gray-300 mb-1.5">
              <Server className="w-4 h-4 text-gray-500" /> Tracker API URL
              <span className={`w-1.5 h-1.5 rounded-full ml-auto ${state.trackerConnected ? 'bg-emerald-400' : 'bg-red-400'}`} />
            </label>
            <div className="flex gap-2">
              <input value={trackerInput} onChange={e => setTrackerInput(e.target.value)}
                className="flex-1 bg-[#0f1117] border border-[#2a2d3a] rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 outline-none" />
              <button onClick={testTracker} disabled={testingTracker}
                className="px-3 py-2 text-xs bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 rounded-lg disabled:opacity-50 transition-colors whitespace-nowrap">
                {testingTracker ? 'Testing...' : 'Test'}
              </button>
            </div>
          </div>
          <div>
            <label className="flex items-center gap-2 text-sm text-gray-300 mb-1.5">
              <HardDrive className="w-4 h-4 text-gray-500" /> Peer Agent URL
              <span className={`w-1.5 h-1.5 rounded-full ml-auto ${state.peerConnected ? 'bg-emerald-400' : 'bg-red-400'}`} />
            </label>
            <div className="flex gap-2">
              <input value={peerInput} onChange={e => setPeerInput(e.target.value)}
                className="flex-1 bg-[#0f1117] border border-[#2a2d3a] rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 outline-none" />
              <button onClick={testPeer} disabled={testingPeer}
                className="px-3 py-2 text-xs bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 rounded-lg disabled:opacity-50 transition-colors whitespace-nowrap">
                {testingPeer ? 'Testing...' : 'Test'}
              </button>
            </div>
          </div>
          <div className="flex items-center gap-2 pt-2">
            <button onClick={handleSave} className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors">
              {saved ? <CheckCircle2 className="w-4 h-4" /> : <Save className="w-4 h-4" />} {saved ? 'Saved!' : 'Save'}
            </button>
            <button onClick={handleReset} className="inline-flex items-center gap-2 px-4 py-2 bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 text-sm rounded-lg transition-colors">
              <RotateCcw className="w-4 h-4" /> Reset
            </button>
          </div>
        </div>
      </div>

      {/* System Info */}
      {state.peerStatus && (
        <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5">
          <h3 className="text-gray-100 font-semibold mb-4">Peer Agent Info</h3>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Peer ID', state.peerStatus.peer_id],
              ['Status', state.peerStatus.status],
              ['TCP Port', state.peerStatus.tcp_port],
              ['API Port', state.peerStatus.api_port],
              ['Shared Directory', state.peerStatus.shared_dir],
              ['Download Directory', state.peerStatus.download_dir],
              ['Shared Files', state.peerStatus.files_shared],
              ['Active Transfers', state.peerStatus.active_transfers],
            ].map(([label, value]) => (
              <div key={String(label)}>
                <dt className="text-gray-500 text-xs">{String(label)}</dt>
                <dd className="text-gray-200 font-mono text-xs mt-0.5">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* Help */}
      <div className="bg-[#1a1d28] rounded-xl border border-[#2a2d3a] p-5">
        <h3 className="text-gray-100 font-semibold mb-3 flex items-center gap-2"><Info className="w-4 h-4 text-blue-400" /> How It Works</h3>
        <div className="text-sm text-gray-400 space-y-2">
          <p>This dashboard communicates with the Python backend services running on your machine.</p>
          <p>The <strong className="text-gray-300">Tracker Server</strong> manages peer registrations and file discovery. The <strong className="text-gray-300">Peer Agent</strong> handles file sharing and direct TCP transfers.</p>
          <p className="text-gray-500 text-xs mt-3">Note: The browser cannot access local files directly. All file sharing and downloads are performed by the Python peer agent process.</p>
        </div>
      </div>
    </div>
  );
}
