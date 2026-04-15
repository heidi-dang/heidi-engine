## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-04-15 - [Optimized Telemetry State and Pricing Caching]
**Learning:** Redundant disk I/O in telemetry event emission can significantly slow down the training pipeline. Thread-safe caching with a TTL and explicit cache keys for pricing configurations provides measurable speedups (~2x - 25x depending on file presence). Also, redundant and broken cache checks in core state retrieval (like the NameError in `get_state`) can lead to system-wide instability.
**Action:** Always verify cache logic for variable-driven keys (like run IDs) and ensure that performance optimizations do not introduce NameErrors or other regressions. Use module-level caches for frequently accessed, slowly changing configuration data.
