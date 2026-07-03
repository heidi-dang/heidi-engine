## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelizing Subprocess-Heavy Tasks]
**Learning:** Parallelizing subprocess-bound tasks (like unit test execution) via `ThreadPoolExecutor` provides near-linear speedups on multi-core systems because `subprocess` calls release the GIL. However, when injecting code into templates for execution, `textwrap.indent` is critical to prevent `IndentationError` in the generated scripts.
**Action:** Use `ThreadPoolExecutor` for subprocess-bound loops and always use `textwrap.indent` when dynamically constructing Python scripts for execution.
