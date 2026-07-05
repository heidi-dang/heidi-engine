## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelize Unit Test Gate]
**Learning:** Sequential subprocess execution in pipeline loops (like `03_unit_test_gate.py`) is a major performance bottleneck that can be significantly mitigated using `ThreadPoolExecutor` with a CPU-count-based worker pool. Additionally, when combining multiple regex patterns for efficiency, using non-capturing groups `(?:\...)` is essential to prevent `re.findall` from returning tuples and breaking metadata schemas.
**Action:** Prioritize parallelization for I/O or subprocess-heavy loops. Always use non-capturing groups when optimizing regex searches with `findall` to maintain expected string-list output.
