## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelized Pipeline Gates and Safe Code Injection]
**Learning:** Sequential subprocess execution in pipeline gates (like `03_unit_test_gate.py`) is a massive bottleneck. Parallelizing with `ThreadPoolExecutor` and `as_completed` (to maintain progress UI) provides a ~3.4x speedup. When dynamically injecting code into templates for testing, simple f-strings can cause `IndentationError` if the code isn't properly aligned with the wrapper's block structure.
**Action:** Parallelize I/O-bound pipeline stages and use `textwrap.indent` for robust code injection in test wrappers. Always pre-compile regex at the module level for repetitive processing.
