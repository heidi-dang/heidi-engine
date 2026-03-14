import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Mock rich before importing dashboard
mock_rich = MagicMock()
sys.modules["rich"] = mock_rich
sys.modules["rich.console"] = mock_rich
sys.modules["rich.layout"] = mock_rich
sys.modules["rich.live"] = mock_rich
sys.modules["rich.panel"] = mock_rich
sys.modules["rich.style"] = mock_rich
sys.modules["rich.table"] = mock_rich
sys.modules["rich.text"] = mock_rich

from heidi_engine import telemetry
from heidi_engine import dashboard

def test_path_traversal_mitigation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        dashboard.AUTOTRAIN_DIR = tmp_dir

        test_cases = [
            ("/etc/passwd", "passwd"),
            ("../../etc/passwd", "passwd"),
            ("run_123", "run_123"),
        ]

        for run_id, expected_name in test_cases:
            # Telemetry
            path_tel = telemetry.get_run_dir(run_id)
            assert path_tel == Path(tmp_dir) / "runs" / expected_name

            # Dashboard
            path_dash = dashboard.get_run_dir(run_id)
            assert path_dash == Path(tmp_dir) / "runs" / expected_name
