#!/usr/bin/env python3
"""Start a P2P peer agent."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.peer_main import create_app
import uvicorn

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Start P2P Peer Agent')
    parser.add_argument('--peer-id', default=None, help='Unique peer ID')
    parser.add_argument('--tcp-port', type=int, default=9001, help='TCP port for file transfers')
    parser.add_argument('--api-port', type=int, default=8001, help='API port for control')
    parser.add_argument('--tracker-url', default='http://localhost:8000', help='Tracker server URL')
    parser.add_argument('--shared-dir', default='./shared', help='Directory to share files from')
    parser.add_argument('--download-dir', default='./downloads', help='Directory to download files to')
    args = parser.parse_args()
    
    app = create_app(
        peer_id=args.peer_id,
        tcp_port=args.tcp_port,
        api_port=args.api_port,
        tracker_url=args.tracker_url,
        shared_dir=args.shared_dir,
        download_dir=args.download_dir
    )
    
    print(f'Starting P2P Peer Agent on API port {args.api_port}, TCP port {args.tcp_port}')
    uvicorn.run(app, host='0.0.0.0', port=args.api_port)
