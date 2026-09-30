## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-09-30 - [Optimized Pricing Configuration Loading in Telemetry]
**Learning:** Frequent API cost estimation checks during high-frequency telemetry tracking trigger repeated disk existence checks (`pricing_file.exists()`) and JSON parsing. Thread-safe in-memory caching with a short TTL (5.0s) reduces disk I/O and JSON overhead by ~20x while maintaining configuration responsiveness.
**Action:** Always wrap disk-bound configuration file lookups called from hot event/telemetry tracking paths in a thread-safe TTL cache.
