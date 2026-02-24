
import os
import sys
import importlib.util
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch, mock_open

# Add scripts directory to path to import 03_unit_test_gate
scripts_dir = str(Path(__file__).parent.parent / "scripts")
sys.path.append(scripts_dir)

# Import 03_unit_test_gate using importlib because it starts with a digit
spec = importlib.util.spec_from_file_location("unit_test_gate", os.path.join(scripts_dir, "03_unit_test_gate.py"))
unit_test_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit_test_gate)

from heidi_engine.telemetry import get_run_dir

class TestSecurityHarden:
    """Test security hardening measures."""

    def test_dangerous_patterns_detection(self):
        """Test that dangerous patterns are correctly identified."""
        dangerous_codes = [
            "import os",
            "import subprocess",
            "from sys import exit",
            "eval('print(1)')",
            "exec('import os')",
            "__import__('os')",
            "getattr(os, 'system')",
            "open('test.txt', 'w')",
            "open('test.txt', 'a')",
            "import requests",
            "import socket",
        ]

        for code in dangerous_codes:
            is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
            assert is_dangerous, f"Code should be dangerous: {code}"
            assert len(patterns) > 0

    def test_safe_patterns_allowed(self):
        """Test that safe patterns are allowed."""
        safe_codes = [
            "print('hello')",
            "def add(a, b): return a + b",
            "class MyClass: pass",
            "x = [i for i in range(10)]",
            "open('test.txt', 'r')",
            "open('test.txt')",
        ]

        for code in safe_codes:
            is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
            # Safe code should pass our BASIC check
            assert not is_dangerous, f"Code should be safe: {code}. Found patterns: {patterns}"

    @patch("subprocess.run")
    def test_environment_isolation(self, mock_run, tmp_path):
        """Test that subprocess environment is isolated."""
        mock_run.return_value = MagicMock(stdout="__EXECUTION_SUCCESS__\n", stderr="", returncode=0)

        # We need to set a dummy environment variable that should NOT be passed
        os.environ["SECRET_KEY_FOR_TEST"] = "hidden-secret"

        unit_test_gate.test_python_code("print('hello')", str(tmp_path), execution_timeout=5)

        # Check the env passed to subprocess.run
        args, kwargs = mock_run.call_args
        passed_env = kwargs.get("env", {})

        assert "SECRET_KEY_FOR_TEST" not in passed_env
        assert "PATH" in passed_env
        assert "PYTHONPATH" in passed_env
        assert passed_env["PYTHONPATH"] == str(tmp_path)

    def test_run_id_path_sanitization(self):
        """Test that run_id is sanitized to prevent path traversal."""
        traversal_id = "../../../tmp/evil"
        run_dir = get_run_dir(traversal_id)

        # It should only use the basename "evil"
        assert run_dir.name == "evil"
        assert ".." not in run_dir.name

    def test_indentation_fix(self, tmp_path):
        """Test that code is correctly indented in the wrapper."""
        code = "print('line1')\nprint('line2')"
        temp_dir = str(tmp_path)

        m = mock_open()
        with patch("builtins.open", m):
            unit_test_gate.test_python_code(code, temp_dir)

            # Check what was written to the file
            written_content = ""
            for call in m().write.call_args_list:
                written_content += call[0][0]

            assert "    print('line1')" in written_content
            assert "    print('line2')" in written_content
            assert "\ntry:\n" in written_content
