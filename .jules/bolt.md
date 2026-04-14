## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Telemetry State and Pricing Lookups]
**Learning:** High-frequency polling of telemetry state and pricing configuration can become an I/O bottleneck. Furthermore, even seemingly "cheap" operations like `Path` object construction and `.absolute()` calls trigger syscall overhead that adds up on hot paths. String-based cache keys are significantly faster than those involving `Path` objects.
**Action:** Use thread-safe module-level caches for configuration and state lookups with appropriate TTLs. Favor string-based cache keys over `Path` objects in performance-critical sections to minimize syscall overhead.
