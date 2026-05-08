## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-08 - [Dashboard and Telemetry I/O Optimization]
**Learning:** High-frequency polling in TUIs (like the Heidi Dashboard) can create significant disk I/O bottlenecks if every refresh triggers a full state read and glob-based file lookup. Caching these with short TTLs (0.5s-1.0s) drastically reduces system overhead without sacrificing perceived real-time responsiveness.
**Action:** Always use short-lived TTL caches for state and file-system lookups in monitoring tools that refresh multiple times per second.
