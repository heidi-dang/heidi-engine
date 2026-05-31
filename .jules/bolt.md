## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-23 - [Optimized Telemetry Pricing and Redaction]
**Learning:** Caching the pricing configuration with a short TTL (5s) avoids redundant disk I/O and JSON parsing for every telemetry event, providing a ~7x speedup for cost estimation. Additionally, pre-compiling regex patterns for redaction yields a measurable ~1.5x speedup for log processing.
**Action:** Implement short-lived caches for configuration files that are read frequently in hot paths, and always pre-compile regex objects at the module level.
