#!/usr/bin/env python3
"""Start the P2P tracker server."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
import uvicorn

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Start P2P Tracker Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    args = parser.parse_args()
    
    print(f'Starting P2P Tracker Server on {args.host}:{args.port}')
    uvicorn.run(app, host=args.host, port=args.port)
