## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelized Unit Test Execution]
**Learning:** Subprocess execution for unit testing generated code is a major sequential bottleneck in the pipeline. Thread-safe parallelization with a sensible worker cap (min(CPU, 8)) provides a ~3-4x speedup on typical developer machines without exhausting system resources.
**Action:** Parallelize independent I/O-bound or subprocess-heavy tasks using ThreadPoolExecutor while ensuring thread-safety with locks for shared state (like telemetry counters).
