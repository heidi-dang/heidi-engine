## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-04-16 - [Thread-safe Caching for Pricing Configuration]
**Learning:** In performance-critical paths like token cost estimation, repeated disk I/O for configuration files (even small ones) adds measurable latency. Using a thread-safe module-level cache with a TTL provides a significant speedup while allowing for configuration updates.
**Action:** Implement thread-safe caching for configuration loading on hot paths to reduce syscall overhead.
