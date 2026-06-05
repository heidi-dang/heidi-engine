## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-22 - [Parallelized Code Validation Pipeline]
**Learning:** Parallelizing subprocess execution (unit test gate) using `ThreadPoolExecutor` provides the most significant performance gain for the training loop (~3.6x speedup). Pre-compiling regex for both positive (keyword) and negative (dangerous pattern) scans significantly reduces CPU overhead during dataset validation.
**Action:** Parallelize IO-bound or subprocess-heavy pipeline stages and use combined regex fast-paths for multi-pattern scans.
