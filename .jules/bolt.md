## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelizing IO-Bound Subprocess Gates]
**Learning:** Subprocess-heavy scripts like the unit test gate are major sequential bottlenecks. Parallelizing them with `ThreadPoolExecutor` (capped to avoid resource exhaustion) provides a near-linear speedup (~3.7x on 4 cores). Combined regex fast-paths for security scanning further reduce CPU overhead for clean samples (~5.8x speedup).
**Action:** Identify pipeline stages involving external processes or IO and parallelize them early. Use combined regex fast-paths to skip expensive individual pattern matching for the common "safe" case.
