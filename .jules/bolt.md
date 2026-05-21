## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-20 - [Fixing Broken Cache Optimization]
**Learning:** High-performance code paths (like telemetry caches) are often less tested and more prone to "refactoring" bugs like NameError from undefined variables.
**Action:** Always verify "fast-path" logic with specific unit tests that exercise both cache hits and misses.
