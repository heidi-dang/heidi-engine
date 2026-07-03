## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelized Unit Testing Gate]
**Learning:** Subprocess execution for unit testing is a significant sequential bottleneck. Parallelizing with `ThreadPoolExecutor` and optimizing regex patterns (pre-compilation + combination) yielded a ~2.3x speedup on a 4-core system.
**Action:** Always consider `ThreadPoolExecutor` for independent subprocess-heavy tasks and utilize pre-compiled, combined regex patterns to minimize overhead.
