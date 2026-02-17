"""HTTP server module for Heidi Engine dashboard."""

import argparse
import sys


def main():
    """CLI entry point for HTTP server."""
    parser = argparse.ArgumentParser(
        description="Heidi Engine HTTP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Security: Defaults to localhost only for security.
         Use --host 0.0.0.0 only in trusted environments.
        """
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )
    
    args = parser.parse_args()
    
    print(f"Heidi Engine HTTP Server v0.1.0")
    print(f"Starting server on {args.host}:{args.port}")
    print("Note: Server functionality not implemented yet")


if __name__ == "__main__":
    main()
