import os
import shutil
import subprocess
import sys
import tempfile

from pygments.lexers import guess_lexer


def guess_language(code: str) -> str:
    """Guess programming language from snippet."""
    try:
        lexer = guess_lexer(code)
        return lexer.name.lower()
    except Exception:
        return "unknown"

def validate_code(language: str, code: str) -> bool:
    """
    Validate code snippet by attempting to compile or parse it.
    Returns True if valid (or unknown language), False if invalid.
    """
    if not code or not code.strip():
        return False

    try:
        if language == "python":
            return _validate_python(code)
        elif language == "cpp":
            return _validate_cpp(code)
        elif language == "go":
            return _validate_go(code)
        elif language == "javascript":
            return _validate_javascript(code)
        else:
            # Unknown language, assume valid to avoid blocking
            print(f"[WARN] Validation skipped: Unsupported language '{language}'", file=sys.stderr)
            return True
    except Exception as e:
        print(f"[WARN] Validation error for {language}: {e}", file=sys.stderr)
        return False

def _validate_python(code: str) -> bool:
    try:
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError:
        return False

def _validate_cpp(code: str) -> bool:
    if not shutil.which("g++"):
        return True # Skip if compiler not found

    with tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", delete=False) as f:
        f.write(code)
        cpp_path = f.name

    exe_path = cpp_path + ".exe"
    try:
        # Try to compile only (no link) to be faster and safer
        subprocess.run(["g++", "-fsyntax-only", cpp_path], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        if os.path.exists(cpp_path):
            os.unlink(cpp_path)
        if os.path.exists(exe_path):
            os.unlink(exe_path)

def _validate_go(code: str) -> bool:
    if not shutil.which("go"):
        return True

    with tempfile.NamedTemporaryFile(suffix=".go", mode="w", delete=False) as f:
        # Unpack code into main package if needed, or just write it
        if "package " not in code:
            f.write("package main\n" + code)
        else:
            f.write(code)
        go_path = f.name

    try:
        # go vet is good but might require module setup.
        # 'go tool compile' is lower level.
        # Let's try simple formatting which does syntax check
        subprocess.run(["gofmt", "-e", go_path], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        if os.path.exists(go_path):
            os.unlink(go_path)

def _validate_javascript(code: str) -> bool:
    if not shutil.which("node"):
        return True

    with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False) as f:
        f.write(code)
        js_path = f.name

    try:
        # node --check (syntax check only)
        subprocess.run(["node", "--check", js_path], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        if os.path.exists(js_path):
            os.unlink(js_path)
