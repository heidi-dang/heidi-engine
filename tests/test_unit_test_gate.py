import importlib
import tempfile
import pytest

unit_test_gate = importlib.import_module("scripts.03_unit_test_gate")


def test_dangerous_patterns_importlib():
    code = "import importlib\nos = importlib.import_module('os')"
    is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
    assert is_dangerous
    assert len(patterns) > 0


def test_dangerous_patterns_builtins():
    code = "import builtins\nbuiltins.eval('1+1')"
    is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
    assert is_dangerous
    assert len(patterns) > 0


def test_dangerous_patterns_open_keyword_mode():
    code = "open(file='secret.txt', mode='w')"
    is_dangerous, patterns = unit_test_gate.check_dangerous_code(code)
    assert is_dangerous
    assert len(patterns) > 0


def test_test_python_code_indentation():
    code = "def add(a, b):\n    return a + b\n\nres = add(2, 3)\nprint(res)"
    with tempfile.TemporaryDirectory() as tmp_dir:
        passed, stdout, stderr = unit_test_gate.test_python_code(code, tmp_dir)
        assert passed
        assert "5" in stdout
