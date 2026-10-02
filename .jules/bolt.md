## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-10-02 - [Thread-safe TTL Cache for Pricing Configuration]
**Learning:** Frequent calls to estimate_cost() in usage tracking loops incurred repeated disk checks (pricing_file.exists()) and JSON parsing. Adding a thread-safe 5s TTL cache validated against file mtime reduced 10,000 calls from ~358ms to ~256ms (~1.4x speedup) while returning shallow inner-dict copies to preserve immutability.
**Action:** When caching dictionary objects in hot paths, validate mtime to prevent stale state and return shallow copies (e.g. {k: v.copy() for k, v in cache.items()}) instead of copy.deepcopy() to avoid unnecessary reflection overhead.
