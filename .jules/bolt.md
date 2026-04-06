## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-23 - [Thread-Safe Pricing Cache with Path Isolation]
**Learning:** Global caches in multi-run environments must be keyed by unique context identifiers (like file paths) to prevent cross-run data leakage. Shallow copies of nested dictionaries lead to state corruption; `copy.deepcopy` is essential for cache isolation.
**Action:** When implementing module-level caches for nested data structures, use `copy.deepcopy` for both storage and retrieval, and ensure cache keys provide sufficient isolation for different execution contexts.
