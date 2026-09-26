import importlib
import pytest

gate = importlib.import_module("scripts.03_unit_test_gate")


def test_dangerous_patterns_importlib():
    code = "import importlib; os = importlib.import_module('os'); os.system('whoami')"
    is_dangerous, patterns = gate.check_dangerous_code(code)
    assert is_dangerous
    assert len(patterns) > 0


def test_dangerous_patterns_builtins():
    code = "import builtins; builtins.__import__('os').system('id')"
    is_dangerous, patterns = gate.check_dangerous_code(code)
    assert is_dangerous
    assert len(patterns) > 0


def test_dangerous_patterns_ctypes():
    code = "import ctypes; ctypes.CDLL(None)"
    is_dangerous, patterns = gate.check_dangerous_code(code)
    assert is_dangerous
    assert len(patterns) > 0


def test_dangerous_patterns_open_keyword_mode():
    code = "with open('/tmp/evil.txt', mode='w') as f:\n    f.write('evil')"
    is_dangerous, patterns = gate.check_dangerous_code(code)
    assert is_dangerous
    assert len(patterns) > 0
