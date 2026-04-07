## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2024-05-15 - [Optimized Pricing Configuration Lookup]
**Learning:** `load_pricing_config` was a bottleneck due to disk I/O on every event emission. Additionally, `copy.deepcopy` is significantly slower (~300x in stress tests) than `.copy()` for dictionaries. For flat configuration data, a shallow copy is often sufficient to prevent external mutation of the cache.
**Action:** Implement thread-safe TTL caching for configuration lookups and prefer `.copy()` over `deepcopy()` when only top-level isolation is required in performance-critical paths.
