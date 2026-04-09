## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-01 - [Optimized State and Pricing Caching]
**Learning:** Caching expensive disk I/O and JSON parsing in the telemetry hot-path (like pricing config) significantly reduces overhead during event emission and dashboard polling. A multi-run StateCache with mtime validation provides a ~25x speedup over disk reads while guaranteeing consistency if files are modified externally.
**Action:** Implement TTL-based caching combined with mtime validation for persistent state files to achieve high performance without sacrificing data integrity.
