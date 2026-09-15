import importlib

unit_test_gate = importlib.import_module("scripts.03_unit_test_gate")
check_dangerous_code = unit_test_gate.check_dangerous_code


def test_dangerous_code_detection():
    # Test safe code
    safe_code = """
def add(a, b):
    return a + b
"""
    is_dangerous, matches = check_dangerous_code(safe_code)
    assert not is_dangerous
    assert len(matches) == 0

    # Test dangerous imports
    dangerous_import_1 = "import importlib\nmod = importlib.import_module('os')"
    is_dangerous, matches = check_dangerous_code(dangerous_import_1)
    assert is_dangerous

    dangerous_import_2 = "from builtins import eval as my_eval"
    is_dangerous, matches = check_dangerous_code(dangerous_import_2)
    assert is_dangerous

    # Test existing dangerous patterns
    dangerous_os = "import os\nos.system('ls')"
    is_dangerous, _ = check_dangerous_code(dangerous_os)
    assert is_dangerous

    dangerous_eval = "x = eval('1 + 1')"
    is_dangerous, _ = check_dangerous_code(dangerous_eval)
    assert is_dangerous
