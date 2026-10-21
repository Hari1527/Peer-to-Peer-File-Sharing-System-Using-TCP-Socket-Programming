#!/bin/bash
set -e

echo "=== P2P File Sharing Demo ==="
echo ""

# Create directories
mkdir -p shared_peer1 shared_peer2 downloads_peer1 downloads_peer2

# Create sample files
echo "Hello from Peer 1!" > shared_peer1/hello.txt
dd if=/dev/urandom of=shared_peer1/random.bin bs=1024 count=100 2>/dev/null
echo "This is a test document." > shared_peer1/document.txt

echo "Sample file from Peer 2" > shared_peer2/peer2_file.txt

# Function to cleanup
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $TRACKER_PID $PEER1_PID $PEER2_PID 2>/dev/null || true
    wait $TRACKER_PID $PEER1_PID $PEER2_PID 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT

# Start tracker
echo "Starting tracker on port 8000..."
python3 scripts/start_tracker.py --port 8000 &
TRACKER_PID=$!
sleep 2

# Start peer 1
echo "Starting Peer 1 (API: 8001, TCP: 9001)..."
python3 scripts/start_peer.py --peer-id peer1 --tcp-port 9001 --api-port 8001 --shared-dir ./shared_peer1 --download-dir ./downloads_peer1 &
PEER1_PID=$!
sleep 2

# Start peer 2
echo "Starting Peer 2 (API: 8002, TCP: 9002)..."
python3 scripts/start_peer.py --peer-id peer2 --tcp-port 9002 --api-port 8002 --shared-dir ./shared_peer2 --download-dir ./downloads_peer2 &
PEER2_PID=$!
sleep 2

echo ""
echo "=== All services running ==="
echo "Tracker:  http://localhost:8000"
echo "Peer 1:   http://localhost:8001 (TCP: 9001)"
echo "Peer 2:   http://localhost:8002 (TCP: 9002)"
echo ""
echo "Try these commands:"
echo "  curl http://localhost:8000/api/health"
echo "  curl http://localhost:8000/api/peers"
echo "  curl http://localhost:8000/api/files"
echo "  curl http://localhost:8001/api/peer/status"
echo "  curl http://localhost:8001/api/peer/files"
echo ""
echo "To download a file from peer1 to peer2:"
echo '  curl -X POST http://localhost:8002/api/peer/download -H "Content-Type: application/json" -d '\''{"file_id": "<file_id>", "peer_id": "peer1", "filename": "hello.txt"}'\'
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for any process to exit
wait
