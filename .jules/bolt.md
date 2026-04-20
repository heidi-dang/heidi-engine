## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-22 - [Optimized Telemetry Pricing Caching]
**Learning:** On performance-critical paths in Python, constructing `Path` objects and calling `.absolute()` repeatedly triggers syscall overhead and object creation churn. Caching these results in a thread-safe manner provides significant speedups for repeated configuration lookups.
**Action:** Use thread-safe caching for configuration loading that involves disk I/O, especially when called frequently in cost estimation or telemetry loops.
