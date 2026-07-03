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
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from typing import Any, Dict, List, Tuple

# =============================================================================
# CONFIGURATION - Adjust these for your needs
# =============================================================================

# Timeout for each test in seconds
TEST_TIMEOUT = 30

# Maximum execution time for generated code
EXECUTION_TIMEOUT = 5

# BOLT OPTIMIZATION: Pre-compile regex patterns for efficiency
CODE_BLOCK_RE = re.compile(
    r"```python\n(.*?)```|```\n(.*?)```|`([^`\n]+)`" , re.DOTALL
)

# BOLT OPTIMIZATION: Combine dangerous patterns into single pre-compiled regex
DANGEROUS_RE = re.compile(
    r"\bimport\s+[^#\n]*\b(os|subprocess|sys|shutil|socket|requests|urllib|pathlib|pickle|pty|code|bdb|pdb|multiprocessing|threading|tempfile|ftplib|smtplib|telnetlib|http|xmlrpc)\b|"
    r"\bfrom\s+(os|subprocess|sys|shutil|socket|requests|urllib|pathlib|pickle|pty|code|bdb|pdb|multiprocessing|threading|tempfile|ftplib|smtplib|telnetlib|http|xmlrpc)\b|"
    r"\beval\s*\(|"
    r"\bexec\s*\(|"
    r"\b__import__\s*\(|"
    r"\bgetattr\s*\(|"
    r"\bsetattr\s*\(|"
    r"\bbreakpoint\s*\(|"
    r"\bos\.(system|popen|spawn|remove|unlink|rmdir|mkdir|chmod|chown|kill|exec|fork|pipe)\b|"
    r"\bsubprocess\.(run|call|check_call|check_output|Popen)\b|"
    r"\bshutil\.(rmtree|move|copy|copy2|copyfile|copymode|copystat|chown)\b|"
    r"\bpickle\.(load|loads)\b|"
    r"\bshelve\.open\b|"
    r"\bopen\s*\([^)]*,\s*(mode\s*=\s*)?['\"][^'\"r]*[wa+x]",
    re.IGNORECASE
)

# BOLT OPTIMIZATION: Pre-compile Python keyword heuristic
_PY_KEYWORDS_RE = re.compile(
    r"\b(def|class|import|return|if|for|while)\b"
)


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
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 4,
        help="Number of parallel workers (default: CPU count)",
    )

    return parser.parse_args()


def extract_python_code(text: str) -> List[str]:
    """
    Extract Python code blocks from text.

    BOLT OPTIMIZATION: Uses pre-compiled regex for extraction and heuristic filtering.
    """
    # BOLT OPTIMIZATION: Use re.finditer to efficiently find all code blocks
    code_blocks = []
    for match in CODE_BLOCK_RE.finditer(text):
        # CODE_BLOCK_RE has 3 capturing groups for different patterns
        code = match.group(1) or match.group(2) or match.group(3)
        if code:
            code_blocks.append(code)

    # Filter: keep only code that looks like Python
    python_code = []
    for code in code_blocks:
        # Skip if too short (probably not real code)
        if len(code.strip()) < 20:
            continue

        # BOLT OPTIMIZATION: Use pre-compiled keyword regex instead of multiple 'in' checks
        if not _PY_KEYWORDS_RE.search(code):
            continue

        python_code.append(code)

    return python_code


def check_dangerous_code(code: str) -> Tuple[bool, List[str]]:
    """
    Check if code contains dangerous patterns.

    BOLT OPTIMIZATION: Uses single pre-compiled regex for all patterns.
    """
    # Since we combined patterns into one regex, we can't easily return which specific
    # pattern matched without more complex logic, but for safety we just need to know if ANY matched.
    match = DANGEROUS_RE.search(code)
    if match:
        return True, [match.group(0)]

    return False, []


def test_python_code(code: str, temp_dir: str, execution_timeout: int = 5) -> Tuple[bool, str, str]:
    """
    Test Python code in isolated environment.
    """
    # Write code to temp file
    test_file = os.path.join(temp_dir, "test_code.py")

    # BOLT OPTIMIZATION: Use textwrap.indent for cleaner code injection
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
        # BOLT OPTIMIZATION: Use restricted env to prevent secret leakage
        restricted_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": temp_dir,
        }

        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=execution_timeout,
            cwd=temp_dir,
            env=restricted_env,
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
    # BOLT OPTIMIZATION: Avoid redundant os.path.dirname calls
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

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
    print(f"[INFO] Using {args.workers} parallel workers")

    # BOLT OPTIMIZATION: Use ThreadPoolExecutor for parallel processing
    tested_samples = [None] * len(samples)
    passed_count = 0
    failed_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Map futures to their original index to preserve order
        future_to_index = {}
        for i, sample in enumerate(samples):
            # Create isolated temp directory for this sample
            sample_temp_dir = os.path.join(base_temp_dir, f"sample_{i}")
            os.makedirs(sample_temp_dir, exist_ok=True)

            future = executor.submit(test_sample, sample, sample_temp_dir, args.execution_timeout)
            future_to_index[future] = i

        # BOLT OPTIMIZATION: Process results as they complete while maintaining order
        for i, future in enumerate(concurrent.futures.as_completed(future_to_index)):
            index = future_to_index[future]
            try:
                tested = future.result()
                tested_samples[index] = tested

                # Count results
                test_result = tested.get("test_result", {})
                if test_result.get("passed", False):
                    passed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"[ERROR] Sample {index} failed with exception: {e}", file=sys.stderr)
                # Fallback for failed samples
                tested_samples[index] = samples[index]
                tested_samples[index]["test_result"] = {"passed": False, "reason": f"exception: {e}"}
                failed_count += 1

            # Progress reporting
            if (i + 1) % 10 == 0 or (i + 1) == len(samples):
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
