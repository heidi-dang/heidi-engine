import importlib.util
import os
import sys

# Import 03_unit_test_gate using importlib since module name starts with digits
spec = importlib.util.spec_from_file_location("unit_test_gate", os.path.join("scripts", "03_unit_test_gate.py"))
unit_test_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit_test_gate)


def test_dangerous_pattern_detection():
    # Dangerous import test cases
    dangerous_snippets = [
        "import importlib",
        "import builtins",
        "import ctypes",
        "import codecs",
        "from importlib import import_module",
        "importlib.import_module('os')",
        "eval('2 + 2')",
        "exec('import os')",
        "open('test.txt', 'w')",
        "open('test.txt', mode='a')",
    ]

    for snippet in dangerous_snippets:
        is_dangerous, patterns = unit_test_gate.check_dangerous_code(snippet)
        assert is_dangerous, f"Expected '{snippet}' to be flagged as dangerous"

    # Safe snippet test cases
    safe_snippets = [
        "def add(a, b):\n    return a + b",
        "import math\nprint(math.sqrt(16))",
        "open('test.txt', 'r')",
    ]

    for snippet in safe_snippets:
        is_dangerous, patterns = unit_test_gate.check_dangerous_code(snippet)
        assert not is_dangerous, f"Expected '{snippet}' to be safe, but flagged: {patterns}"
