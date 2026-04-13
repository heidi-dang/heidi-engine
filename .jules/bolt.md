## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-04-13 - [Pricing Config Cache Optimization]
**Learning:** High-frequency telemetry events that calculate costs can bottleneck on disk I/O if the pricing configuration is re-read from disk on every call. Even with fast SSDs, the overhead of Path construction and JSON parsing adds up. Using a thread-safe, module-level cache with a short TTL (2.0s) and a fast cache key (based on environment variables rather than absolute path resolution) yields a ~25x performance improvement.
**Action:** Implement thread-safe caching for configuration lookups on telemetry hot-paths, ensuring cache keys are derived from readily available state (like env vars) to avoid expensive syscalls.
