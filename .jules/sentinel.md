## 2025-01-24 - Hardening Unit Test Gate Security
**Vulnerability:** The `scripts/03_unit_test_gate.py` script was vulnerable to multiple security risks when executing generated code:
1. **Environment Leakage:** Subprocesses inherited the full parent environment, potentially exposing sensitive keys like `OPENAI_API_KEY`.
2. **Regex Bypasses:** Dangerous pattern matching used weak regexes (e.g., `eval\s*\(`) that could be bypassed with syntax like `(eval)(...)`.
3. **Missing Blocks:** Crucial modules like `importlib`, `builtins`, and `ctypes` were not blacklisted.

**Learning:** Regex-based blacklisting for code execution is fragile but can be improved by using word boundaries (`\b`) and strict environment isolation. Additionally, user code wrapping must handle indentation correctly to avoid syntax errors.

**Prevention:**
- Always use a strict allowlist for environment variables when running untrusted code in a subprocess.
- Use `\b` word boundaries in regexes to prevent simple obfuscation bypasses.
- Indent user-provided code using `textwrap.indent` before injecting it into a `try...except` block template.

## 2025-01-24 - Fixed NameError in Telemetry Cache
**Vulnerability:** A `NameError` in `heidi_engine/telemetry.py` caused a crash when attempting to retrieve state, due to an undefined variable `target_run_id` in a redundant cache check block.
**Learning:** Redundant and poorly tested "optimization" blocks can introduce critical failures.
**Prevention:** Ensure all branches of a performance optimization are covered by unit tests. Removed the broken redundant block as it was already covered by a correct cache check earlier in the function.
