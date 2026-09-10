"""
Unit tests for security pattern checks in unit test gate script (03_unit_test_gate.py).
"""

import importlib.util
from pathlib import Path


def _import_unit_test_gate():
    script_path = Path(__file__).parent.parent / "scripts" / "03_unit_test_gate.py"
    spec = importlib.util.spec_from_file_location("unit_test_gate", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


unit_test_gate = _import_unit_test_gate()


class TestDangerousCodeDetection:
    """Test detection of dangerous code patterns in generated outputs."""

    def test_importlib_blocked(self):
        """Test that importlib imports are flagged as dangerous."""
        code = "import importlib\nmod = importlib.import_module('os')"
        is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
        assert is_dangerous, "importlib should be flagged as dangerous"

    def test_from_builtins_blocked(self):
        """Test that importing from builtins is flagged as dangerous."""
        code = "from builtins import eval\neval('1+1')"
        is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
        assert is_dangerous, "from builtins should be flagged as dangerous"

    def test_open_write_mode_blocked(self):
        """Test that open() in write/append mode is flagged as dangerous."""
        code = "with open('secret.txt', 'w') as f:\n    f.write('data')"
        is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
        assert is_dangerous, "open() in write mode should be flagged as dangerous"

        code_kw = "f = open('secret.txt', mode='a+')"
        is_dangerous_kw, _ = unit_test_gate.check_dangerous_code(code_kw)
        assert is_dangerous_kw, "open() with mode keyword in append mode should be flagged"

    def test_safe_code_passed(self):
        """Test that standard benign code passes check_dangerous_code."""
        code = "def add(a, b):\n    return a + b\n\nprint(add(2, 3))"
        is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
        assert not is_dangerous, "Safe math function should not be flagged"
