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
    - Binds to 127.0.0.1 only
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
        help="Host to bind to (IGNORED — server will bind to 127.0.0.1 for security)",
    )
    args = parser.parse_args()

    # Enforce loopback-only binding for security. If user passed a different host,
    # we ignore it and warn rather than binding to a non-loopback interface.
    display_host = "127.0.0.1"
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        import sys

        print(
            f"Warning: --host={args.host} ignored; server will bind to {display_host} for security",
            file=sys.stderr,
        )

    from heidi_engine.telemetry import start_http_server

    print(f"Starting HTTP status server on {display_host}:{args.port}")
    print("Endpoints:")
    print(f"  - Status: http://{display_host}:{args.port}/status")
    print(f"  - Health:  http://{display_host}:{args.port}/health")
    print("\nPress Ctrl+C to stop\n")

    # start_http_server(port) already binds to 127.0.0.1 — keep that behavior.
    start_http_server(args.port)

    # Keep process alive until interrupted
    try:
        import time

        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
