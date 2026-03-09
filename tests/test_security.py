import os
from pathlib import Path
from heidi_engine import telemetry

def test_run_id_path_traversal_sanitization():
    """
    Test that malicious run_id inputs are correctly sanitized to prevent
    path traversal outside the intended AUTOTRAIN_DIR/runs directory.
    """
    autotrain_dir = Path(telemetry.AUTOTRAIN_DIR).resolve()

    # Test cases: (input_run_id, expected_in_path)
    test_cases = [
        ("../../../../../etc/passwd", "passwd"),
        ("/absolute/path", "path"),
        (".", "default"),
        ("..", "default"),
        ("", "default"),
        ("valid_run_123", "valid_run_123"),
    ]

    for run_id_input, expected_component in test_cases:
        run_dir = telemetry.get_run_dir(run_id_input)
        resolved_run_dir = run_dir.resolve()

        # Ensure it's still under AUTOTRAIN_DIR/runs
        assert str(resolved_run_dir).startswith(str(autotrain_dir / "runs")), \
            f"Path traversal detected for input '{run_id_input}': resolved to '{resolved_run_dir}'"

        # Ensure the final component is what we expect
        assert resolved_run_dir.name == expected_component, \
            f"Unexpected sanitization for input '{run_id_input}': expected '{expected_component}', got '{resolved_run_dir.name}'"

def test_dashboard_uses_sanitized_paths(tmp_path):
    """
    Test that dashboard.py correctly uses sanitized path management from telemetry.
    """
    from heidi_engine import dashboard

    # Override AUTOTRAIN_DIR for testing
    telemetry.AUTOTRAIN_DIR = str(tmp_path)

    malicious_run_id = "../../malicious"

    # These should all be sanitized via telemetry calls
    run_dir = dashboard.get_run_dir(malicious_run_id)
    events_path = dashboard.get_events_path(malicious_run_id)
    state_path = dashboard.get_state_path(malicious_run_id)

    assert ".." not in str(run_dir)
    assert run_dir.name == "malicious"
    assert events_path.name == "events.jsonl"
    assert state_path.name == "state.json"
    assert str(events_path.parent).endswith("malicious")
