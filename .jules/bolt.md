## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Telemetry Pricing Config Caching]
**Learning:** Loading and parsing JSON configuration files (like pricing models) in high-frequency event paths (every token update) introduces significant cumulative disk I/O and CPU overhead. A thread-safe module-level cache with a short TTL (5.0s) is enough to eliminate 99%+ of these redundant operations.
**Action:** Identify and cache configuration lookups in high-frequency loops, even if the files are small.
