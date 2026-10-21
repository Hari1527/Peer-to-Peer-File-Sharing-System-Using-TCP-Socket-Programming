import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { TrackerApiService } from '../services/trackerApi';
import { PeerApiService } from '../services/peerApi';
import { WebSocketManager } from '../services/websocket';
import type { PeerStatus } from '../types/peer';
import type { TrackerStats, AppNotification, ActivityLogEntry, WebSocketEvent } from '../types/events';
import {
  DEFAULT_TRACKER_URL, DEFAULT_PEER_URL,
  DEFAULT_TRACKER_WS_URL, DEFAULT_PEER_WS_URL,
  REFRESH_INTERVAL, MAX_ACTIVITY_LOGS, STORAGE_KEYS,
} from '../utils/constants';

function stored(key: string, fallback: string): string {
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}

function wsUrlFromHttp(httpUrl: string): string {
  try {
    const u = new URL(httpUrl);
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:';
    u.pathname = '/ws/events';
    return u.toString();
  } catch { return httpUrl.replace(/^http/, 'ws') + '/ws/events'; }
}

interface AppState {
  trackerUrl: string;
  peerUrl: string;
  trackerConnected: boolean;
  peerConnected: boolean;
  peerStatus: PeerStatus | null;
  trackerStats: TrackerStats | null;
  notifications: AppNotification[];
  activityLogs: ActivityLogEntry[];
}

interface AppContextValue {
  state: AppState;
  trackerApi: TrackerApiService;
  peerApi: PeerApiService;
  setTrackerUrl: (url: string) => void;
  setPeerUrl: (url: string) => void;
  addNotification: (type: AppNotification['type'], message: string) => void;
  removeNotification: (id: string) => void;
  clearActivityLogs: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

let notifId = 0;

function eventToLog(event: WebSocketEvent): ActivityLogEntry {
  const categoryMap: Record<string, ActivityLogEntry['category']> = {
    peer_registered: 'peer', peer_offline: 'peer', peer_heartbeat: 'peer',
    file_shared: 'file',
    transfer_started: 'transfer', transfer_progress: 'transfer',
    transfer_completed: 'transfer', transfer_failed: 'transfer',
  };
  const severityMap: Record<string, ActivityLogEntry['severity']> = {
    peer_registered: 'info', peer_offline: 'warning', peer_heartbeat: 'info',
    file_shared: 'success',
    transfer_started: 'info', transfer_progress: 'info',
    transfer_completed: 'success', transfer_failed: 'error',
  };
  const msgMap: Record<string, string> = {
    peer_registered: `Peer ${(event.data as Record<string,string>).peer_id || ''} registered`,
    peer_offline: `Peer ${(event.data as Record<string,string>).peer_id || ''} went offline`,
    peer_heartbeat: `Heartbeat from ${(event.data as Record<string,string>).peer_id || ''}`,
    file_shared: `File shared: ${(event.data as Record<string,string>).filename || ''}`,
    transfer_started: `Transfer started: ${(event.data as Record<string,string>).filename || ''}`,
    transfer_progress: `Transfer progress: ${(event.data as Record<string,string>).filename || ''}`,
    transfer_completed: `Transfer completed: ${(event.data as Record<string,string>).filename || ''}`,
    transfer_failed: `Transfer failed: ${(event.data as Record<string,string>).filename || ''}`,
  };
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: event.timestamp || new Date().toISOString(),
    type: event.type,
    category: categoryMap[event.type] || 'system',
    severity: severityMap[event.type] || 'info',
    peer_id: (event.data as Record<string,string>).peer_id,
    message: msgMap[event.type] || event.type,
    data: event.data,
  };
}

export function AppContextProvider({ children }: { children: React.ReactNode }) {
  const [trackerUrl, setTrackerUrlState] = useState(() => stored(STORAGE_KEYS.TRACKER_URL, DEFAULT_TRACKER_URL));
  const [peerUrl, setPeerUrlState] = useState(() => stored(STORAGE_KEYS.PEER_URL, DEFAULT_PEER_URL));
  const [trackerConnected, setTrackerConnected] = useState(false);
  const [peerConnected, setPeerConnected] = useState(false);
  const [peerStatus, setPeerStatus] = useState<PeerStatus | null>(null);
  const [trackerStats, setTrackerStats] = useState<TrackerStats | null>(null);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLogEntry[]>([]);

  const trackerApiRef = useRef(new TrackerApiService(trackerUrl));
  const peerApiRef = useRef(new PeerApiService(peerUrl));
  const trackerWsRef = useRef(new WebSocketManager(wsUrlFromHttp(trackerUrl), 'tracker'));
  const peerWsRef = useRef(new WebSocketManager(wsUrlFromHttp(peerUrl), 'peer'));

  const setTrackerUrl = useCallback((url: string) => {
    setTrackerUrlState(url);
    try { localStorage.setItem(STORAGE_KEYS.TRACKER_URL, url); } catch { /* */ }
    trackerApiRef.current.setBaseUrl(url);
    trackerWsRef.current.setUrl(wsUrlFromHttp(url));
  }, []);

  const setPeerUrl = useCallback((url: string) => {
    setPeerUrlState(url);
    try { localStorage.setItem(STORAGE_KEYS.PEER_URL, url); } catch { /* */ }
    peerApiRef.current.setBaseUrl(url);
    peerWsRef.current.setUrl(wsUrlFromHttp(url));
  }, []);

  const addNotification = useCallback((type: AppNotification['type'], message: string) => {
    const n: AppNotification = { id: String(++notifId), type, message, timestamp: new Date().toISOString() };
    setNotifications(prev => [n, ...prev].slice(0, 20));
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearActivityLogs = useCallback(() => setActivityLogs([]), []);

  // Polling for health/status
  useEffect(() => {
    let active = true;
    const poll = async () => {
      if (!active) return;
      try {
        await trackerApiRef.current.getHealth();
        if (active) setTrackerConnected(true);
      } catch { if (active) setTrackerConnected(false); }
      try {
        const stats = await trackerApiRef.current.getStats();
        if (active) setTrackerStats(stats);
      } catch { /* keep last stats */ }
      try {
        const status = await peerApiRef.current.getStatus();
        if (active) { setPeerConnected(true); setPeerStatus(status); }
      } catch { if (active) { setPeerConnected(false); setPeerStatus(null); } }
    };
    poll();
    const id = setInterval(poll, REFRESH_INTERVAL);
    return () => { active = false; clearInterval(id); };
  }, [trackerUrl, peerUrl]);

  // WebSocket events
  useEffect(() => {
    const handleEvent = (event: WebSocketEvent) => {
      setActivityLogs(prev => [eventToLog(event), ...prev].slice(0, MAX_ACTIVITY_LOGS));
    };
    const unsub1 = trackerWsRef.current.onEvent(handleEvent);
    const unsub2 = peerWsRef.current.onEvent(handleEvent);
    trackerWsRef.current.connect();
    peerWsRef.current.connect();
    return () => { unsub1(); unsub2(); trackerWsRef.current.disconnect(); peerWsRef.current.disconnect(); };
  }, []);

  const value: AppContextValue = {
    state: { trackerUrl, peerUrl, trackerConnected, peerConnected, peerStatus, trackerStats, notifications, activityLogs },
    trackerApi: trackerApiRef.current,
    peerApi: peerApiRef.current,
    setTrackerUrl, setPeerUrl, addNotification, removeNotification, clearActivityLogs,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used within AppContextProvider');
  return ctx;
}

export function useTrackerApi() {
  return useAppContext().trackerApi;
}

export function usePeerApi() {
  return useAppContext().peerApi;
}
