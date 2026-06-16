## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelizing Subprocess-Heavy Tasks]
**Learning:** For scripts that involve many subprocess executions (like `scripts/03_unit_test_gate.py`), `ThreadPoolExecutor` provides a significant performance boost (~3-5x) even with Python's GIL, as the threads spend most of their time waiting for the OS to manage the subprocesses.
**Action:** Identify I/O-bound or subprocess-bound bottlenecks and apply `ThreadPoolExecutor` with a conservative worker cap (e.g., 8) to balance speedup and resource usage.
