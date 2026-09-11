import importlib.util

# Load 03_unit_test_gate module dynamically (since file name starts with numbers)
spec = importlib.util.spec_from_file_location("unit_test_gate", "scripts/03_unit_test_gate.py")
unit_test_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit_test_gate)

check_dangerous_code = unit_test_gate.check_dangerous_code


def test_importlib_and_builtins_blocked():
    code_importlib = "import importlib\nmod = importlib.import_module('os')"
    is_dangerous, matches = check_dangerous_code(code_importlib)
    assert is_dangerous is True

    code_builtins = "import builtins\nbuiltins.eval('1+1')"
    is_dangerous, matches = check_dangerous_code(code_builtins)
    assert is_dangerous is True

    code_from_ctypes = "from ctypes import c_int"
    is_dangerous, matches = check_dangerous_code(code_from_ctypes)
    assert is_dangerous is True


def test_builtins_attr_blocked():
    code = "b = __builtins__\nb['eval']('1+1')"
    is_dangerous, matches = check_dangerous_code(code)
    assert is_dangerous is True


def test_open_write_modes_blocked():
    code_kw = "with open('foo.txt', mode='w') as f: f.write('bad')"
    is_dangerous, matches = check_dangerous_code(code_kw)
    assert is_dangerous is True

    code_pos = "with open('foo.txt', 'w') as f: f.write('bad')"
    is_dangerous, matches = check_dangerous_code(code_pos)
    assert is_dangerous is True

    code_read = "with open('foo.txt', 'r') as f: data = f.read()"
    is_dangerous, matches = check_dangerous_code(code_read)
    assert is_dangerous is False
