import sys
import os
from pathlib import Path

# Add the project root to sys.path to import heidi_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from heidi_engine.telemetry import sanitize_run_id as telemetry_sanitize
from heidi_engine.dashboard import sanitize_run_id as dashboard_sanitize

def test_telemetry_sanitization():
    _perform_sanitization_check(telemetry_sanitize, "telemetry_sanitize")

def test_dashboard_sanitization():
    _perform_sanitization_check(dashboard_sanitize, "dashboard_sanitize")

def _perform_sanitization_check(sanitize_func, name):
    print(f"Testing {name}...")

    # Normal cases
    assert sanitize_func("run_123") == "run_123"
    assert sanitize_func("valid-id") == "valid-id"

    # Malicious cases
    assert sanitize_func("../../etc/passwd") == "passwd"
    assert sanitize_func("..") == "invalid_run_id"
    assert sanitize_func(".") == "invalid_run_id"
    assert sanitize_func("/") == "invalid_run_id"
    assert sanitize_func("") == "invalid_run_id"
    assert sanitize_func(None) == "invalid_run_id"

    print(f"All {name} tests passed!")

if __name__ == "__main__":
    try:
        test_telemetry_sanitization()
        test_dashboard_sanitization()
        print("\nSUCCESS: Path traversal protection is working correctly.")
    except AssertionError as e:
        print(f"\nFAILURE: Sanitization test failed!")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
        sys.exit(1)
