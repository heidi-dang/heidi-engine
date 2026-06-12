## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-20 - [Parallelized Unit Test Execution]
**Learning:** The unit test gate stage is a major sequential bottleneck due to subprocess execution for each sample. Parallelizing this stage using `ThreadPoolExecutor` with a capped worker count (e.g., 8) provides a significant speedup (measured ~3.4x with 4 workers) without overwhelming system resources.
**Action:** Identify sequential stages involving I/O or subprocesses and parallelize them using `ThreadPoolExecutor` while ensuring thread-safe resource isolation (e.g., unique temp directories).
