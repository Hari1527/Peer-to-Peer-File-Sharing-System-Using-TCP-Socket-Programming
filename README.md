# Peer-to-Peer File Sharing System Using TCP Socket Programming

A complete, high-performance, decentralized peer-to-peer (P2P) file-sharing application built from scratch in Python and TypeScript/React. The system couples a lightweight central tracker for peer discovery and file metadata indexing with custom raw TCP socket file transfers, cryptographic integrity validation (SHA-256), multi-threaded streaming, real-time WebSockets, and a developer-tools dashboard.

---

## 📑 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [TCP Socket Wire Protocol](#-tcp-socket-wire-protocol)
- [Key Features & Engineering Highlights](#-key-features--engineering-highlights)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
  - [Tracker Server Endpoints](#tracker-server-endpoints)
  - [Peer Control Endpoints](#peer-control-endpoints)
  - [WebSocket Event Stream](#websocket-event-stream)
- [Frontend Dashboard](#-frontend-dashboard)
- [Quick Start](#-quick-start)
  - [Automated Full Stack Launch](#1-automated-full-stack-launch)
  - [Manual Step-by-Step Launch](#2-manual-step-by-step-launch)
- [Automated Testing](#-automated-testing)
- [End-to-End Verification](#-end-to-end-verification)
- [Portfolio & Design Insights](#-portfolio--design-insights)

---

## 🏛 Architecture

The system is organized into three logical tiers:

```mermaid
flowchart TD
    subgraph TrackerTier ["Tracker Server (:8000)"]
        T_API["FastAPI Registry & Search Engine"]
        T_DB[("SQLite Metadata Database\n(Peers, Files, Transfer History)")]
        T_WS["WebSocket Event Hub\n(/ws/events)"]
        T_EXP["Periodic Stale Peer Reaper"]
        
        T_API <--> T_DB
        T_API --> T_WS
        T_EXP --> T_DB
    end

    subgraph Peer1Tier ["Peer Agent 1 (:8001 / TCP :9001)"]
        P1_CTRL["FastAPI Control API (:8001)"]
        P1_TCP_S["Multi-threaded TCP Server (:9001)"]
        P1_TCP_C["TCP Download Client"]
        P1_IDX["File Scanner & SHA-256 Hasher"]
        P1_MGR["Transfer Manager"]
        P1_DIR[("Shared Folder\n./shared_peer1")]
        
        P1_IDX --> P1_DIR
        P1_TCP_S --> P1_DIR
        P1_CTRL --> P1_MGR
        P1_CTRL --> P1_IDX
    end

    subgraph Peer2Tier ["Peer Agent 2 (:8002 / TCP :9002)"]
        P2_CTRL["FastAPI Control API (:8002)"]
        P2_TCP_S["Multi-threaded TCP Server (:9002)"]
        P2_TCP_C["TCP Download Client"]
        P2_DOWN[("Downloads Folder\n./downloads_peer2")]
        P2_MGR["Transfer Manager"]
        
        P2_CTRL --> P2_MGR
        P2_TCP_C --> P2_DOWN
    end

    subgraph FrontendTier ["Developer Dashboard (:5173)"]
        UI["React 19 + Vite + Tailwind CSS"]
        CTX["AppContext & WebSocket Manager"]
        PAGES["Overview | Files | Peers | Transfers | Activity | Settings"]
        
        UI --> CTX
        CTX --> PAGES
    end

    %% Interactions
    P1_CTRL -- "1. Register & Periodic Heartbeat" --> T_API
    P2_CTRL -- "1. Register & Periodic Heartbeat" --> T_API
    P2_CTRL -- "2. Query Files & Peer Lookup" --> T_API
    P2_TCP_C == "3. DIRECT TCP STREAMING (Binary Framed Protocol)" ==> P1_TCP_S
    P2_CTRL -- "4. Report Transfer Metrics" --> T_API
    
    UI -. "REST & WebSocket Control" .-> P1_CTRL
    UI -. "REST & WebSocket Registry" .-> T_API
```

1. **Tracker Server**:
   - Maintains active peer registrations, hosts, TCP ports, and last-seen timestamps.
   - Manages indexed file metadata (file size, SHA-256 fingerprint, peer associations).
   - Reaps offline peers automatically after heartbeat timeout expiration.
   - **Never touches file payloads** — maintains true zero-relay decentralization.
   - Broadcasts real-time events over WebSockets (`/ws/events`).

2. **Peer Agents**:
   - Each peer is an autonomous process running:
     - A **TCP File Server** listening on raw sockets for binary transfer requests.
     - A **TCP File Client** connecting directly to remote peers for chunked downloads.
     - A **File Indexer** that computes SHA-256 hashes and watches local files.
     - A **Transfer Manager** that tracks progress, speed, and cancels transfers safely.
     - A **Control API** allowing local UI and CLI control with CORS support.

3. **Web Interface**:
   - Modern React 19 + TypeScript + Vite + Tailwind CSS dashboard.
   - Dark developer-tools UI inspired by Wireshark and modern cloud consoles.
   - Configurable peer targeting: seamlessly switch between local peer instances.

---

## ⚡ TCP Socket Wire Protocol

Instead of relying on HTTP file downloads or third-party transfer libraries, this project implements a custom binary framing protocol using Python's standard `socket` library.

### Wire Header (8 Bytes Fixed)

Every message transmitted over TCP begins with an 8-byte fixed-size header packed in network byte order (Big-Endian):

| Offset | Field | Type | Description |
|:---|:---|:---|:---|
| `0..1` | Magic Bytes | `2 Bytes` | Always ASCII `'P'`, `'2'` (`0x50 0x32`) |
| `2` | Protocol Version | `1 Byte` | Current version: `0x01` |
| `3` | Message Type | `1 Byte` | Opcode defining the packet purpose |
| `4..7` | Payload Length | `4 Bytes` (uint32) | Size of the upcoming message payload in bytes |

### Message Types & Opcodes

| Hex | Name | Payload Content | Direction |
|:---|:---|:---|:---|
| `0x01` | `FILE_REQUEST` | JSON: `{"file_id": string, "filename": string, "offset": int}` | Downloader → Uploader |
| `0x02` | `FILE_RESPONSE` | JSON: `{"status": "ok"|"error", "size": int, "checksum": string}` | Uploader → Downloader |
| `0x03` | `CHUNK_DATA` | Binary chunk payload (up to 64 KB per chunk) | Uploader → Downloader |
| `0x04` | `TRANSFER_COMPLETE`| JSON: `{"status": "success", "bytes_sent": int, "checksum": string}` | Uploader → Downloader |
| `0x05` | `TRANSFER_ABORT` | JSON: `{"reason": string}` | Bidirectional |
| `0x06` | `ERROR` | JSON: `{"code": int, "message": string}` | Bidirectional |

### Transfer Flow Sequence

```mermaid
sequenceDiagram
    autonumber
    participant D as Downloader (TCP Client)
    participant U as Uploader (TCP Server)

    D->>U: Connect TCP Socket (IP:Port)
    D->>U: [Header 8B: TYPE=0x01, LEN=N] + JSON Payload (file_id, filename, offset=0)
    U->>U: Validate path & file existence, retrieve SHA-256
    U->>D: [Header 8B: TYPE=0x02, LEN=M] + JSON Payload (status=ok, size=bytes, checksum)
    
    loop Stream in 64KB Chunks
        U->>D: [Header 8B: TYPE=0x03, LEN=ChunkSize] + Raw Binary Data
        D->>D: Update local SHA-256 digest & progress counters
    end
    
    U->>D: [Header 8B: TYPE=0x04, LEN=K] + JSON Payload (status=success, checksum)
    D->>D: Verify calculated SHA-256 matches header checksum
    D->>U: Gracefully close connection (FIN/ACK)
```

---

## 🛡 Key Features & Engineering Highlights

- **Direct Peer-to-Peer TCP Streaming**: Files are transferred chunk-by-chunk directly between peers without proxying through the tracker.
- **Cryptographic File Verification**: SHA-256 checksums are calculated upon scanning and verified byte-by-byte upon download completion.
- **Path Traversal Protection**: File requests reject null bytes, directory escaping (`../`), absolute paths, and restricted filesystem characters.
- **Thread Concurrency & Non-blocking I/O**: Python `threading` with thread-safe synchronization primitives ensures multiple simultaneous downloads and uploads do not block the node.
- **Resilient Heartbeat & Expiration**: Peers ping the tracker every 15 seconds. If a peer terminates abruptly, the tracker reaps it after 45 seconds of silence.
- **Persistent Metadata**: Tracker persists peers, indexed files, and transfer audit logs in an SQLite database using thread-safe context managers.
- **Live Event Broadcasting**: Real-time push notifications over WebSockets inform connected dashboards of peer events, file discoveries, and transfer progress.
- **Interactive Multi-Peer Frontend**: The web interface allows real-time file searching, peer inspection, manual/automated transfers, live speed gauges, and dynamic switching between local peer nodes.

---

## 🛠 Technology Stack

### Backend
- **Python**: 3.11+ (Tested on Python 3.14)
- **FastAPI**: REST API Framework
- **Uvicorn**: High-performance ASGI Server
- **Socket**: Python Standard Library TCP Sockets
- **Threading**: Native concurrent connection handling
- **SQLite3**: ACID persistent metadata store
- **Pydantic v2**: Strict schema validation & serialization
- **Pytest**: 68 comprehensive unit and integration tests

### Frontend
- **React 19**: Modern UI library
- **TypeScript**: Strict compile-time type safety
- **Vite 6**: Fast next-gen build tool
- **Tailwind CSS v4**: Modern CSS styling
- **React Router v7**: Client-side SPA navigation
- **Lucide Icons**: Clean developer-tool icons
- **Native WebSockets**: Real-time activity telemetry

---

## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI REST and WebSocket routes
│   │   │   ├── peer.py           # Peer control endpoints
│   │   │   ├── tracker.py        # Central tracker endpoints
│   │   │   └── websocket.py      # Real-time event broadcaster
│   │   ├── core/                 # Networking and transfer engine
│   │   │   ├── file_index.py     # Local directory scanner & SHA-256 hasher
│   │   │   ├── peer_client.py    # HTTP client for peer-to-tracker requests
│   │   │   ├── tcp_client.py     # Custom TCP socket binary downloader
│   │   │   ├── tcp_protocol.py   # 8-byte binary framing wire protocol
│   │   │   ├── tcp_server.py     # Multi-threaded TCP socket file server
│   │   │   ├── tracker_service.py# Tracker business logic & peer manager
│   │   │   └── transfer_manager.py# Concurrency, status, and rate tracking
│   │   ├── db/
│   │   │   └── database.py       # Thread-safe SQLite repository
│   │   ├── schemas/              # Pydantic v2 data models
│   │   │   ├── file.py
│   │   │   ├── peer.py
│   │   │   └── transfer.py
│   │   ├── utils/                # Security, hashing, and logging
│   │   ├── config.py             # Tracker & Peer settings
│   │   ├── main.py               # Tracker server entry point
│   │   └── peer_main.py          # Peer agent entry point
│   ├── scripts/
│   │   ├── start_tracker.py      # Standalone tracker launcher
│   │   ├── start_peer.py         # Configurable peer launcher
│   │   └── run_demo.sh           # CLI multi-peer demo script
│   ├── tests/                    # 68 automated pytest suites
│   ├── requirements.txt
│   └── tracker.db
│
├── frontend/
│   ├── src/
│   │   ├── app/                  # App shell and React Router
│   │   ├── components/
│   │   │   ├── activity/         # Real-time WebSocket activity feed
│   │   │   ├── dashboard/        # Stats cards, active peers, transfers
│   │   │   ├── files/            # File browser, inspect modal, download
│   │   │   ├── layout/           # Sidebar, TopBar, Toast notifications
│   │   │   ├── peers/            # Peer grid and status indicators
│   │   │   ├── transfers/        # Progress bars, transfer rows, cancellation
│   │   │   └── ui/               # Status badges, skeletons, modals
│   │   ├── context/              # AppContext, WebSockets, notification state
│   │   ├── hooks/                # useApi, useInterval hooks
│   │   ├── services/             # Type-safe API and WebSocket clients
│   │   ├── types/                # TypeScript interface definitions
│   │   └── utils/                # Formatting, byte conversions, constants
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── run_all.sh                    # One-command full-stack launcher
└── README.md                     # Portfolio documentation
```

---

## 📡 API Reference

### Tracker Server Endpoints (`http://localhost:8000`)

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/health` | Service health status and version |
| `GET` | `/api/peers` | List online / offline peers (`?status=online`) |
| `POST` | `/api/peers/register` | Register peer address, TCP port, and shared files |
| `POST` | `/api/peers/heartbeat` | Keep-alive ping preventing timeout expiration |
| `DELETE` | `/api/peers/{peer_id}`| Gracefully unregister peer and remove file index |
| `GET` | `/api/files` | Paginated catalog of all shared files |
| `GET` | `/api/files/search` | Search files by name substring (`?q=term`) |
| `GET` | `/api/files/{id}/peers` | Retrieve online peers hosting a specific file |
| `GET` | `/api/transfers` | Global completed/failed transfer audit history |
| `POST` | `/api/transfers/report` | Peers report completed transfer metrics |
| `GET` | `/api/stats` | Aggregated network statistics |
| `WS` | `/ws/events` | Real-time WebSocket event stream |

### Peer Control Endpoints (`http://localhost:8001` / `:8002`)

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/peer/status` | Current peer configuration, ports, and stats |
| `GET` | `/api/peer/files` | List files in local shared folder |
| `POST` | `/api/peer/share` | Re-scan local directory and publish to tracker |
| `POST` | `/api/peer/refresh` | Trigger instantaneous file indexing |
| `POST` | `/api/peer/download` | Initiate direct TCP download from target peer |
| `GET` | `/api/peer/transfers` | List active, completed, and failed local transfers |
| `GET` | `/api/peer/transfers/{id}` | Real-time progress and speed for a transfer |
| `POST` | `/api/peer/transfers/{id}/cancel` | Abort an ongoing transfer in progress |
| `WS` | `/ws/events` | Local peer WebSocket event notifications |

### WebSocket Event Stream

Clients subscribing to `/ws/events` receive real-time JSON packets:

```json
{
  "type": "file_shared | peer_registered | transfer_started | transfer_completed",
  "timestamp": "2026-10-21T15:10:45.250Z",
  "data": {
    "peer_id": "peer1",
    "filename": "dataset.tar.gz",
    "bytes": 52428800
  }
}
```

---

## 💻 Frontend Dashboard

The frontend dashboard provides a comprehensive developer-tools interface:

1. **Overview**: Live status pills for Tracker & Peer agents, 4 primary telemetry cards (Online Peers, Total Files, Active Transfers, Total Data Transferred), recent transfers list, and active peer directory.
2. **File Explorer**: Search bar, table showing file name, size, truncated SHA-256 hash, and availability status. Includes a "View Peers" modal and a "Download" modal to choose which peer to download from.
3. **Peers Discovery**: Visual grid of all registered network nodes, IP addresses, TCP ports, last-seen relative timestamps, and shared file counts.
4. **Transfers Monitor**: Filterable view (All / Active / Completed / Failed / Cancelled) with animated progress bars, live transfer speeds (`MB/s`), total duration, and transfer abort triggers.
5. **Activity Log**: Real-time event feed powered by WebSockets, with category filtering (Peers, Files, Transfers) and severity color coding.
6. **Settings**: Dynamic Tracker API & Peer Agent URL configuration with one-click connection tests, local peer diagnostic telemetry, and system explanations.

---

## 🚀 Quick Start

### 1. Automated Full Stack Launch

Run the all-in-one setup script from the root directory:

```bash
chmod +x run_all.sh
./run_all.sh
```

This single command:
1. Provisions sample shared directories and test files for Peer 1 and Peer 2.
2. Starts the **Tracker Server** on `http://localhost:8000`.
3. Starts **Peer 1** (API: `http://localhost:8001`, TCP Socket: `9001`).
4. Starts **Peer 2** (API: `http://localhost:8002`, TCP Socket: `9002`).
5. Launches the **Vite Frontend** on `http://localhost:5173`.
6. Traps `Ctrl+C` to cleanly shut down all services.

Open **http://localhost:5173** in your browser to begin testing.

---

### 2. Manual Step-by-Step Launch

If you prefer to run each component in separate terminal windows:

#### Step 1: Install Dependencies

```bash
# Python backend
cd backend
python3 -m pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

#### Step 2: Start Tracker Server
```bash
cd backend
python3 scripts/start_tracker.py --port 8000
```

#### Step 3: Start Peer Agent 1
```bash
cd backend
mkdir -p shared_peer1 downloads_peer1
echo "Hello from Peer 1!" > shared_peer1/hello.txt
python3 scripts/start_peer.py --peer-id peer1 --tcp-port 9001 --api-port 8001 --shared-dir ./shared_peer1 --download-dir ./downloads_peer1
```

#### Step 4: Start Peer Agent 2
```bash
cd backend
mkdir -p shared_peer2 downloads_peer2
python3 scripts/start_peer.py --peer-id peer2 --tcp-port 9002 --api-port 8002 --shared-dir ./shared_peer2 --download-dir ./downloads_peer2
```

#### Step 5: Start Frontend Dashboard
```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:5173` to control the network.

---

## 🧪 Automated Testing

The backend includes a comprehensive pytest suite covering security, wire protocol parsing, TCP transfers, file indexing, tracker persistence, and end-to-end integration:

```bash
cd backend
python3 -m pytest tests/ -v
```

### Test Coverage Highlights:
- **`test_tcp_protocol.py`**: Packet header packing/unpacking, malformed frames, magic byte validation, large payload handling.
- **`test_security.py`**: Path traversal blocking, filename sanitation, illegal directory access prevention.
- **`test_hashing.py`**: SHA-256 chunked calculation, verification of identical/corrupted data.
- **`test_file_index.py`**: Directory scanning, file change detection, file removal handling.
- **`test_transfer.py`**: Transfer status machine, thread-safe concurrent progress updates, cancellations.
- **`test_tracker.py` & `test_tracker_api.py`**: Registration, peer lookups, search filtering, heartbeat updates, stale reaper.
- **`test_e2e.py`**: Multi-peer file sharing and direct binary transfer over TCP sockets with cryptographic verification.

```
============================== 68 passed in 5.50s ==============================
```

Frontend type-safety and bundle verification:
```bash
cd frontend
npx tsc --noEmit
npx vite build
```

---

## 🔬 End-to-End Verification

You can verify the entire direct TCP socket transfer pipeline from the command line:

```bash
# 1. Search for available files on Tracker
curl -s http://localhost:8000/api/files | jq .

# 2. Tell Peer 2 to download a file from Peer 1 directly over TCP
curl -X POST http://localhost:8002/api/peer/download \
  -H "Content-Type: application/json" \
  -d '{"file_id": "<FILE_ID>", "peer_id": "peer1", "filename": "welcome.txt"}'

# 3. Check Peer 2 transfer progress
curl -s http://localhost:8002/api/peer/transfers | jq .

# 4. Verify downloaded file contents and SHA-256 match
shasum -a 256 backend/shared_peer1/welcome.txt
shasum -a 256 backend/downloads_peer2/welcome.txt
```

---
