## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-14 - [Indentation and Syntax Errors in Generated Code Execution]
**Learning:** Injected code within a `try/except` block must be properly indented, otherwise it will fail with a `SyntaxError`.
**Action:** Use `textwrap.indent` to ensure that any dynamically injected code follows the required indentation of its surrounding block.
