## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-22 - [Parallelized Unit Test Gate]
**Learning:** The unit test gate was a major sequential bottleneck because it spawned a new subprocess for every sample. Since these tests are independent and I/O-bound (blocking on subprocess execution), parallelization with `ThreadPoolExecutor` yields a ~3x-5x speedup.
**Action:** Identify I/O-bound sequential loops that spawn subprocesses or make API calls and parallelize them using `ThreadPoolExecutor` while ensuring thread-safe resource isolation (e.g., unique temp directories).
