/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TRACKER_URL: string;
  readonly VITE_PEER_URL: string;
  readonly VITE_TRACKER_WS_URL: string;
  readonly VITE_PEER_WS_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
