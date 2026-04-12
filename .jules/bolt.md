## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Telemetry Caching Optimization]
**Learning:** Caching configuration data (like pricing) that is used in the telemetry hot-path can significantly reduce I/O overhead. Additionally, broken caching logic in state lookups (like the NameError in get_state) can silently degrade performance by falling back to disk reads on every call.
**Action:** Implement thread-safe TTL caching for frequently accessed configuration and state files, and verify that caching logic is actually functional through benchmarks.
