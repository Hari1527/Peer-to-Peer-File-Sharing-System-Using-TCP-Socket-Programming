import type { WebSocketEvent } from '../types/events';
import { WS_RECONNECT_DELAY, WS_MAX_RECONNECT_DELAY } from '../utils/constants';

type EventCallback = (event: WebSocketEvent) => void;
type StatusCallback = () => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private name: string;
  private eventCbs = new Set<EventCallback>();
  private connectCbs = new Set<StatusCallback>();
  private disconnectCbs = new Set<StatusCallback>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private delay = WS_RECONNECT_DELAY;
  private shouldReconnect = true;
  private _connected = false;

  constructor(url: string, name: string) {
    this.url = url;
    this.name = name;
  }

  get connected() { return this._connected; }

  setUrl(url: string) {
    if (url === this.url) return;
    this.url = url;
    this.disconnect();
    this.connect();
  }

  connect() {
    this.shouldReconnect = true;
    this.cleanup();
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        this._connected = true;
        this.delay = WS_RECONNECT_DELAY;
        this.connectCbs.forEach(cb => cb());
      };
      this.ws.onclose = () => {
        this._connected = false;
        this.disconnectCbs.forEach(cb => cb());
        this.scheduleReconnect();
      };
      this.ws.onerror = () => {
        /* onclose will fire after this */
      };
      this.ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data) as WebSocketEvent;
          this.eventCbs.forEach(cb => cb(event));
        } catch { /* ignore malformed messages */ }
      };
    } catch {
      this.scheduleReconnect();
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    this.cleanup();
  }

  onEvent(cb: EventCallback)      { this.eventCbs.add(cb);      return () => { this.eventCbs.delete(cb); }; }
  onConnect(cb: StatusCallback)    { this.connectCbs.add(cb);    return () => { this.connectCbs.delete(cb); }; }
  onDisconnect(cb: StatusCallback) { this.disconnectCbs.add(cb); return () => { this.disconnectCbs.delete(cb); }; }

  private cleanup() {
    if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null; }
    if (this.ws) {
      this.ws.onopen = this.ws.onclose = this.ws.onerror = this.ws.onmessage = null;
      try { this.ws.close(); } catch { /* */ }
      this.ws = null;
    }
    this._connected = false;
  }

  private scheduleReconnect() {
    if (!this.shouldReconnect) return;
    this.reconnectTimer = setTimeout(() => { this.connect(); }, this.delay);
    this.delay = Math.min(this.delay * 1.5, WS_MAX_RECONNECT_DELAY);
  }
}
