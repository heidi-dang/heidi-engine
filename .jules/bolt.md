## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [State Caching and Mutable Data Pitfalls]
**Learning:** When caching complex nested structures (like the telemetry `state.json`), shallow copies (`dict.copy()`) allow callers to mutate objects stored inside the cache (cache pollution). This leads to corrupted state and race conditions. Furthermore, when using optional arguments like `run_id=None`, ensure resolution to the actual ID happens BEFORE cache invalidation.
**Action:** Use `copy.deepcopy()` for caches of nested mutable data. Always resolve dynamic identifiers (like `run_id`) to their concrete values before performing cache operations to ensure key consistency.
