#!/usr/bin/env python3
"""
================================================================================
heidi_engine/http.py - HTTP Status Server Entry Point
================================================================================

Simple entry point to start the HTTP status server.

Usage:
    python -m heidi_engine.http              # Default port 7779
    python -m heidi_engine.http --port 8080  # Custom port
    python -m heidi_engine.http --help        # Help

Security:
    - Binds to specified host (defaults to 127.0.0.1)
    - Returns redacted state only
    - No secrets exposed
================================================================================
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="heidi-engine http",
        description="Heidi Engine HTTP Status Server"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=7779, help="Port to listen on (default: 7779)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (defaults to 127.0.0.1)",
    )
    args = parser.parse_args()

    from heidi_engine.telemetry import start_http_server

    print(f"Starting HTTP status server on {args.host}:{args.port}")
    print("Endpoints:")
    print(f"  - Status: http://{args.host}:{args.port}/status")
    print(f"  - Health:  http://{args.host}:{args.port}/health")
    print("\nPress Ctrl+C to stop\n")

    # start_http_server(port) defaults to 127.0.0.1 but can be overridden.
    start_http_server(args.port, host=args.host)

    # Keep process alive until interrupted
    try:
        import time

        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
