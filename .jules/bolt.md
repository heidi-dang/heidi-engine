## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-01 - [Multi-run State and Pricing Caching]
**Learning:** Implementing a multi-run write-through cache for state and a TTL-based cache for pricing configuration avoids redundant disk I/O and JSON parsing, yielding ~25x speedup for state retrieval and ~2.4x for run listing.
**Action:** Use `st_mtime` for robust cache validation and provide write-through updates to eliminate stale reads in high-frequency polling scenarios.
