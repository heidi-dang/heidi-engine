## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2025-05-15 - [Regex Pre-compilation and Broken Cache Removal]
**Learning:** Pre-compiling regex patterns into module-level constants provides a measurable speedup (~40%) in hot-path string processing like secret redaction. Also, "optimizations" that use undefined variables (like the `target_run_id` bug in `get_state`) can lead to critical failures in production and should be removed or fixed during performance audits.
**Action:** Always verify that cached values are actually used and that the cache lookup logic doesn't introduce NameErrors or redundant I/O.
