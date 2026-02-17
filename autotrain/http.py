#!/usr/bin/env python3
"""
================================================================================
autotrain/http.py - HTTP Status Server Entry Point
================================================================================

Simple entry point to start the HTTP status server.

Usage:
    python -m autotrain.http              # Default port 7779
    python -m autotrain.http --port 8080  # Custom port
    python -m autotrain.http --help        # Help

Security:
    - Binds to 127.0.0.1 only
    - Returns redacted state only
    - No secrets exposed
================================================================================
"""

import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="AutoTrain HTTP Status Server")
    parser.add_argument("--port", "-p", type=int, default=7779, help="Port to listen on (default: 7779)")
    args = parser.parse_args()
    
    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from autotrain.telemetry import start_http_server
    
    host = "127.0.0.1"
    print(f"Starting HTTP status server on {host}:{args.port}")
    print(f"Endpoints:")
    print(f"  - Status: http://{host}:{args.port}/status")
    print(f"  - Health:  http://{host}:{args.port}/health")
    print("")
    print("Press Ctrl+C to stop")
    
    start_http_server(args.port)
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
