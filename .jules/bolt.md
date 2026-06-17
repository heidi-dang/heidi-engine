## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelized Unit Test Gate]
**Learning:** For I/O-bound tasks involving multiple independent subprocess executions (like unit testing generated code), `ThreadPoolExecutor` provides a significant speedup (3x-5x) with minimal complexity. Isolating each execution in its own temporary directory is key to thread safety.
**Action:** Identify sequential loops that execute independent subprocesses or make API calls and parallelize them using `ThreadPoolExecutor`, ensuring strict resource isolation per worker.
