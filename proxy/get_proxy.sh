#!/bin/bash
# Simple wrapper to get the next proxy from the rotator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/rotator.py" | grep "Next proxy:" | awk '{print $3}'
