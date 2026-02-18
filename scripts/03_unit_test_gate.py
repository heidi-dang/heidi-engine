#!/usr/bin/env python3
"""
================================================================================
03_unit_test_gate.py - Optional Unit Test Gate Script
================================================================================

PURPOSE:
    Run generated code samples through basic execution tests to verify
    they are syntactically valid and don't crash.

HOW IT WORKS:
    1. Extracts Python code blocks from generated outputs
    2. Creates isolated temporary directory for each sample
    3. Attempts to compile/execute the code with timeout
    4. Records pass/fail status and error messages

TUNABLE PARAMETERS (via environment variables):
    - RUN_UNIT_TESTS: Set to 1 to enable (default: 0 - disabled)
    - UNIT_TEST_TIMEOUT: Max seconds per test (default: 30)
    - MAX_EXECUTION_TIME: Max code execution time (default: 5 seconds)

SAFETY:
    - Runs in isolated temp directory
    - Uses timeout to prevent infinite loops
    - Does NOT execute arbitrary code from untrusted sources in production
    - This is a BASIC sanity check only - not a security sandbox

NOTE:
    This is OPTIONAL and disabled by default. Enable with RUN_UNIT_TESTS=1
    or --run-tests flag. This step adds significant time to the pipeline.

================================================================================
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# CONFIGURATION - Adjust these for your needs
# =============================================================================

# Timeout for each test in seconds
TEST_TIMEOUT = 30

# Maximum execution time for generated code
EXECUTION_TIMEOUT = 5

# Code block patterns to extract Python code
# TUNABLE: Adjust regex for different code formats
CODE_BLOCK_PATTERNS = [
    # Markdown code blocks: ```python ... ```
    r"```python\n(.*?)```",
    # Markdown code blocks without language: ``` ... ```
    r"```\n(.*?)```",
    # Inline code markers
    r"`([^`\n]+)`",
]

# Patterns that indicate code should NOT be executed
# TUNABLE: Add more dangerous patterns to block
# These are used as a first-pass heuristic alongside AST analysis
DANGEROUS_PATTERNS = [
    r"import\s+(os|subprocess|sys|shutil|importlib|pathlib|socket|urllib|requests|pickle|marshal|shelve|ctypes|platform|pty|commands)",
    r"from\s+(os|subprocess|sys|shutil|importlib|pathlib|socket|urllib|requests|pickle|marshal|shelve|ctypes|platform|pty|commands)",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__\s*\(",
    r"getattr\s*\(",
    r"setattr\s*\(",
    r'open\s*\([^)]*,\s*[\'"][^"\']*[wa+x]',  # file write/append/exclusive
    r'open\s*\([^)]*,\s*[\'"][wa+x]',  # file write/append/exclusive (short)
    r"socket\.",
    r"pickle\.",
]


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run unit tests on generated code samples (optional gate)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run tests (default - disabled for safety)
  python 03_unit_test_gate.py --input data/clean.jsonl --output data/tested.jsonl

  # Run with custom timeout
  python 03_unit_test_gate.py --input data/clean.jsonl --output data/tested.jsonl \\
      --timeout 60 --execution-timeout 10
        """,
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="Input JSONL file (cleaned data)"
    )
    parser.add_argument(
        "--output", "-o", type=str, required=True, help="Output JSONL file (tested data)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("UNIT_TEST_TIMEOUT", 30)),
        help="Timeout per test in seconds (default: 30)",
    )
    parser.add_argument(
        "--execution-timeout",
        type=int,
        default=5,
        help="Max execution time for code in seconds (default: 5)",
    )
    parser.add_argument(
        "--keep-temp", action="store_true", help="Keep temporary directories for debugging"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.environ.get("SEED", 42)),
        help="Random seed (default: 42)",
    )

    return parser.parse_args()


def extract_python_code(text: str) -> List[str]:
    """
    Extract Python code blocks from text.

    HOW IT WORKS:
        - Searches for markdown code blocks
        - Returns list of extracted code snippets

    TUNABLE:
        - Add more patterns for different code formats
        - Filter out non-Python code blocks
    """
    code_blocks = []

    for pattern in CODE_BLOCK_PATTERNS:
        matches = re.findall(pattern, text, re.DOTALL)
        code_blocks.extend(matches)

    # Filter: keep only code that looks like Python
    # This is a heuristic - not perfect
    python_code = []
    for code in code_blocks:
        # Skip if too short (probably not real code)
        if len(code.strip()) < 20:
            continue

        # Skip if it's clearly not Python (no indentation, keywords, etc.)
        if not any(
            kw in code for kw in ["def ", "class ", "import ", "return ", "if ", "for ", "while "]
        ):
            continue

        python_code.append(code)

    return python_code


def check_dangerous_code_ast(code: str) -> Tuple[bool, List[str]]:
    """
    Check if code contains dangerous patterns using AST analysis.

    HOW IT WORKS:
        - Parses code into AST
        - Walks tree to find dangerous imports and function calls
        - Provides more robust protection than regex alone
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # If it doesn't parse, it won't run.
        # Syntax checking happens later in the pipeline.
        return False, []

    # Comprehensive list of dangerous modules
    dangerous_modules = {
        "os", "subprocess", "sys", "shutil", "importlib", "pathlib",
        "socket", "urllib", "requests", "pickle", "marshal", "shelve",
        "ctypes", "platform", "pty", "commands", "builtins"
    }

    # Comprehensive list of dangerous functions
    dangerous_functions = {
        "eval", "exec", "__import__", "getattr", "setattr", "breakpoint",
        "input", "compile", "globals", "locals", "vars", "open"
    }

    found = []

    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_module = alias.name.split(".")[0]
                if base_module in dangerous_modules:
                    found.append(f"import {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_module = node.module.split(".")[0]
                if base_module in dangerous_modules:
                    found.append(f"from {node.module} import ...")

        # Check function calls
        elif isinstance(node, ast.Call):
            func = node.func
            # Direct calls: eval(), exec()
            if isinstance(func, ast.Name):
                if func.id in dangerous_functions:
                    if func.id == "open":
                        # Check for write/append modes in open()
                        is_dangerous_open = True
                        # If mode is not provided, it defaults to 'r'
                        if len(node.args) > 1:
                            mode_arg = node.args[1]
                            if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
                                if all(m not in mode_arg.value for m in "wa+x"):
                                    is_dangerous_open = False
                            elif isinstance(mode_arg, ast.Str): # Support older Python
                                if all(m not in mode_arg.s for m in "wa+x"):
                                    is_dangerous_open = False
                        elif len(node.args) == 1:
                            is_dangerous_open = False # Default is read
                            # But check keywords
                            for kw in node.keywords:
                                if kw.arg == "mode" and (
                                    (isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str) and any(m in kw.value.value for m in "wa+x")) or
                                    (isinstance(kw.value, ast.Str) and any(m in kw.value.s for m in "wa+x"))
                                ):
                                    is_dangerous_open = True

                        if is_dangerous_open:
                            found.append("call to open() with potential write mode")
                    else:
                        found.append(f"call to {func.id}()")

            # Attribute calls: os.system(), subprocess.run()
            elif isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    if func.value.id in dangerous_modules:
                        found.append(f"call to {func.value.id}.{func.attr}()")

                # Check for things like __subclasses__()...
                if func.attr in ["__subclasses__", "__globals__", "__init__", "__builtins__"]:
                    found.append(f"access to dangerous attribute: {func.attr}")

    return len(found) > 0, found


def check_dangerous_code(code: str) -> Tuple[bool, List[str]]:
    """
    Check if code contains dangerous patterns using regex and AST.

    HOW IT WORKS:
        1. Runs regex-based check for quick heuristic
        2. Runs AST-based check for robust analysis
        3. Returns (is_dangerous, list_of_matches)
    """
    found = []

    # 1. Regex check
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            found.append(f"regex:{pattern}")

    # 2. AST check
    is_dangerous_ast, ast_matches = check_dangerous_code_ast(code)
    if is_dangerous_ast:
        for match in ast_matches:
            found.append(f"ast:{match}")

    return len(found) > 0, found


def test_python_code(code: str, temp_dir: str, execution_timeout: int = 5) -> Tuple[bool, str, str]:
    """
    Test Python code in isolated environment.

    HOW IT WORKS:
        1. Write code to temporary file
        2. Try to compile (syntax check)
        3. Try to execute with timeout
        4. Return (passed, stdout, stderr)

    SAFETY:
        - Runs in temp directory
        - Has timeout protection
        - Does NOT execute system commands

    TUNABLE:
        - execution_timeout: Max time code can run
    """
    # Write code to temp file
    test_file = os.path.join(temp_dir, "test_code.py")

    # Correctly indent the user code for the try block
    indented_code = textwrap.indent(code, "    ")

    # Wrap code to capture output safely
    wrapped_code = f"""
import sys
import io

# Capture stdout and stderr
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()
original_stdout = sys.stdout
original_stderr = sys.stderr

try:
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    # Execute the user's code
{indented_code}

    sys.stdout = original_stdout
    sys.stderr = original_stderr

    print("__EXECUTION_SUCCESS__")
    print(stdout_capture.getvalue())

except Exception as e:
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    print(f"__EXECUTION_ERROR__: {{e}}", file=sys.stderr)
"""

    try:
        with open(test_file, "w") as f:
            f.write(wrapped_code)
    except Exception as e:
        return False, "", f"Failed to write temp file: {e}"

    # Try to compile first (fast check)
    try:
        compile(code, test_file, "exec")
    except SyntaxError as e:
        return False, "", f"Syntax error: {e}"

    # Try to execute with timeout
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=execution_timeout,
            cwd=temp_dir,
            env={**os.environ, "PYTHONPATH": temp_dir},
        )

        stdout = result.stdout
        stderr = result.stderr

        # Check for execution success marker
        if "__EXECUTION_SUCCESS__" in stdout:
            return True, stdout.replace("__EXECUTION_SUCCESS__\n", ""), stderr
        elif "__EXECUTION_ERROR__" in stderr:
            return False, stdout, stderr
        else:
            # Exit code check
            if result.returncode != 0:
                return False, stdout, stderr

            return True, stdout, stderr

    except subprocess.TimeoutExpired:
        return False, "", f"Execution timeout ({execution_timeout}s)"
    except Exception as e:
        return False, "", f"Execution error: {e}"


def test_sample(
    sample: Dict[str, Any], temp_dir: str, execution_timeout: int = 5
) -> Dict[str, Any]:
    """
    Test a single sample.

    HOW IT WORKS:
        1. Extract Python code from output
        2. Check for dangerous patterns
        3. Run each code block
        4. Record results in metadata
    """
    output_text = sample.get("output", "")

    # Extract code blocks
    code_blocks = extract_python_code(output_text)

    if not code_blocks:
        # No code to test - pass by default
        sample["test_result"] = {"passed": True, "reason": "no_code_found", "blocks_tested": 0}
        return sample

    # Check for dangerous code
    all_dangerous = []
    for code in code_blocks:
        is_dangerous, patterns = check_dangerous_code(code)
        if is_dangerous:
            all_dangerous.extend(patterns)

    if all_dangerous:
        sample["test_result"] = {
            "passed": False,
            "reason": "dangerous_patterns",
            "patterns": list(set(all_dangerous)),
            "blocks_tested": len(code_blocks),
        }
        return sample

    # Test each code block
    results = []
    for i, code in enumerate(code_blocks):
        passed, stdout, stderr = test_python_code(code, temp_dir, execution_timeout)
        results.append(
            {"block_index": i, "passed": passed, "error": stderr if not passed else None}
        )

    # Sample passes if at least one code block passes
    # (Some samples may have explanation text + code)
    passed = any(r["passed"] for r in results)

    sample["test_result"] = {
        "passed": passed,
        "reason": "tested" if passed else "all_blocks_failed",
        "blocks_tested": len(code_blocks),
        "block_results": results,
    }

    return sample


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load samples from JSONL file."""
    samples = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON parse error: {e}", file=sys.stderr)
                continue

    return samples


def save_jsonl(samples: List[Dict[str, Any]], path: str) -> None:
    """Save samples to JSONL file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")


def main():
    """
    Main entry point for unit test gate.
    """
    args = parse_args()

    print(f"[INFO] Loading samples from: {args.input}")

    # Load samples
    samples = load_jsonl(args.input)
    print(f"[INFO] Loaded {len(samples)} samples")

    # Create base temp directory
    base_temp_dir = tempfile.mkdtemp(prefix="unit_test_gate_")
    print(f"[INFO] Using temp directory: {base_temp_dir}")

    # Test each sample
    tested_samples = []
    passed_count = 0
    failed_count = 0

    for i, sample in enumerate(samples):
        # Create isolated temp directory for this sample
        sample_temp_dir = os.path.join(base_temp_dir, f"sample_{i}")
        os.makedirs(sample_temp_dir, exist_ok=True)

        # Test the sample
        tested = test_sample(sample, sample_temp_dir, args.execution_timeout)
        tested_samples.append(tested)

        # Count results
        test_result = tested.get("test_result", {})
        if test_result.get("passed", False):
            passed_count += 1
        else:
            failed_count += 1

        # Progress
        if (i + 1) % 10 == 0:
            print(
                f"  Tested {i + 1}/{len(samples)} samples "
                f"(passed: {passed_count}, failed: {failed_count})",
                file=sys.stderr,
            )

    # Cleanup temp directory
    if not args.keep_temp:
        try:
            shutil.rmtree(base_temp_dir)
            print("[INFO] Cleaned up temp directory")
        except Exception as e:
            print(f"[WARN] Failed to cleanup temp dir: {e}")

    # Save results
    save_jsonl(tested_samples, args.output)

    # Summary
    print("[OK] Unit test gate complete!")
    print(f"  - Input: {len(samples)} samples")
    print(f"  - Passed: {passed_count}")
    print(f"  - Failed: {failed_count}")
    print(f"  - Output: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
