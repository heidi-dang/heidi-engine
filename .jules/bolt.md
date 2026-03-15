## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Telemetry State and Pricing Management]
**Learning:** Write-through caching in `save_state` combined with TTL-based caching in `get_state` provides a significant performance boost (~20x) for telemetry-heavy applications. Additionally, using `mtime` to cache configuration files like `pricing.json` avoids redundant disk I/O and JSON parsing during hot-path event emission. Removing unnecessary JSON indentation further reduces serialization overhead.
**Action:** Prioritize write-through caching for frequently updated state and use file metadata (mtime) for efficient configuration caching. Avoid pretty-printing JSON in performance-critical paths.
