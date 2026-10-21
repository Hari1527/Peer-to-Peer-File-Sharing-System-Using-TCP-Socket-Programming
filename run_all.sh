#!/usr/bin/env bash
set -e

# Project root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "================================================================="
echo "   P2P File Sharing System Using TCP Socket Programming"
echo "================================================================="
echo ""

# Ensure folders exist
mkdir -p "$ROOT_DIR/backend/shared_peer1" "$ROOT_DIR/backend/shared_peer2"
mkdir -p "$ROOT_DIR/backend/downloads_peer1" "$ROOT_DIR/backend/downloads_peer2"

# Populate sample files if empty
if [ ! -f "$ROOT_DIR/backend/shared_peer1/welcome.txt" ]; then
    echo "Welcome to the Peer-to-Peer File Sharing System!" > "$ROOT_DIR/backend/shared_peer1/welcome.txt"
    echo "This file was transferred directly over raw TCP sockets without relaying through the tracker." >> "$ROOT_DIR/backend/shared_peer1/welcome.txt"
fi

if [ ! -f "$ROOT_DIR/backend/shared_peer1/sample_binary.dat" ]; then
    dd if=/dev/urandom of="$ROOT_DIR/backend/shared_peer1/sample_binary.dat" bs=1024 count=256 2>/dev/null
fi

if [ ! -f "$ROOT_DIR/backend/shared_peer2/peer2_notes.md" ]; then
    echo "# Notes from Peer 2" > "$ROOT_DIR/backend/shared_peer2/peer2_notes.md"
    echo "Distributed systems are resilient, decentralized, and scalable." >> "$ROOT_DIR/backend/shared_peer2/peer2_notes.md"
fi

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down all P2P services..."
    kill $TRACKER_PID $PEER1_PID $PEER2_PID $FRONTEND_PID 2>/dev/null || true
    wait $TRACKER_PID $PEER1_PID $PEER2_PID $FRONTEND_PID 2>/dev/null || true
    echo "✅ All services stopped."
}
trap cleanup EXIT INT TERM

# 1. Start Tracker Server
echo "🚀 [1/4] Starting Tracker Server on port 8000..."
cd "$ROOT_DIR/backend"
python3 scripts/start_tracker.py --port 8000 > /tmp/p2p_tracker.log 2>&1 &
TRACKER_PID=$!
sleep 2

# 2. Start Peer 1
echo "🚀 [2/4] Starting Peer Agent 1 (API: 8001, TCP: 9001)..."
python3 scripts/start_peer.py --peer-id peer1 --tcp-port 9001 --api-port 8001 --shared-dir ./shared_peer1 --download-dir ./downloads_peer1 > /tmp/p2p_peer1.log 2>&1 &
PEER1_PID=$!
sleep 1

# 3. Start Peer 2
echo "🚀 [3/4] Starting Peer Agent 2 (API: 8002, TCP: 9002)..."
python3 scripts/start_peer.py --peer-id peer2 --tcp-port 9002 --api-port 8002 --shared-dir ./shared_peer2 --download-dir ./downloads_peer2 > /tmp/p2p_peer2.log 2>&1 &
PEER2_PID=$!
sleep 1

# 4. Start Frontend
echo "🚀 [4/4] Starting Vite Frontend on port 5173..."
cd "$ROOT_DIR/frontend"
npm run dev -- --host > /tmp/p2p_frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 2

echo ""
echo "================================================================="
echo "   🎉 All P2P Components Are Running!"
echo "================================================================="
echo "   💻 Web UI Dashboard:     http://localhost:5173"
echo "   📡 Tracker API:          http://localhost:8000 (Docs: /docs)"
echo "   🟢 Peer 1 Control API:   http://localhost:8001 (TCP Transfer: 9001)"
echo "   🟢 Peer 2 Control API:   http://localhost:8002 (TCP Transfer: 9002)"
echo "================================================================="
echo ""
echo "💡 Usage Tips:"
echo "   1. Open http://localhost:5173 in your browser to view the dashboard."
echo "   2. Go to 'File Explorer' to see files shared by Peer 1 and Peer 2."
echo "   3. Click 'Download' on any file to pull it directly over TCP sockets."
echo "   4. Switch to Peer 2 in 'Settings' by setting Peer Agent URL to http://localhost:8002"
echo "   5. Check 'Activity' for real-time WebSocket events."
echo ""
echo "Press Ctrl+C to gracefully stop all services."

# Wait indefinitely
wait
