## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-01 - [Parallelized Unit Test Execution]
**Learning:** Sequential subprocess execution (like in `03_unit_test_gate.py`) is a major pipeline bottleneck. Parallelizing with `ThreadPoolExecutor` while ensuring filesystem isolation (unique temp dirs) provides linear speedup for I/O and process-bound tasks.
**Action:** Identify sequential `subprocess.run` loops in processing scripts and parallelize them using `ThreadPoolExecutor` with indexed result mapping to preserve order.
