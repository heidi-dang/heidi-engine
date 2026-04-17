## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Caching Expensive Config Loads]
**Learning:** Thread-safe module-level caching with a TTL is highly effective for reducing disk I/O and JSON parsing overhead in high-frequency functions like `load_pricing_config`. However, constructing `Path` objects and calling `.absolute()` in the cache key path can introduce measurable syscall overhead.
**Action:** Use pre-computed strings or lightweight environment variables for cache keys instead of complex path manipulations on performance-critical paths.
