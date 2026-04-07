import os
import tempfile
import shutil
import importlib.util
import sys

# Load the script starting with digits using importlib
script_path = "scripts/03_unit_test_gate.py"
spec = importlib.util.spec_from_file_location("unit_test_gate", script_path)
unit_test_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit_test_gate)

def test_leak_plugged():
    # Set sensitive environment variable
    os.environ["SENSITIVE_API_KEY"] = "super-secret-key-123"
    os.environ["ANOTHER_TOKEN"] = "token-456"
    os.environ["SAFE_VAR"] = "this is safe"

    # Now that we've fixed the bug and the vulnerability, this should work perfectly.
    code_to_test = "import os\nprint(f'LEAKED_KEY={os.environ.get(\"SENSITIVE_API_KEY\")}')\nprint(f'SAFE_VAR={os.environ.get(\"SAFE_VAR\")}')"

    temp_dir = tempfile.mkdtemp()
    try:
        passed, stdout, stderr = unit_test_gate.test_python_code(code_to_test, temp_dir)

        print(f"Passed: {passed}")
        print(f"Stdout: {stdout.strip()}")

        # Check that key is NOT leaked
        if "LEAKED_KEY=super-secret-key-123" in stdout:
            print("[!] FAIL: Key still leaked!")
            return False

        # Check that key is None
        if "LEAKED_KEY=None" not in stdout:
            print("[!] FAIL: Expected LEAKED_KEY=None")
            return False

        # Check that safe var IS present
        if "SAFE_VAR=this is safe" not in stdout:
            print("[!] FAIL: Safe variable missing!")
            return False

        print("[OK] Success: Leak plugged and safe variables preserved.")
        return True
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if test_leak_plugged():
        sys.exit(0)
    else:
        sys.exit(1)
