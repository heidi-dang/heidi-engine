## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-23 - [Optimized Telemetry State Caching and GPU Status Polling]
**Learning:** Caching long-running subprocess calls like `nvidia-smi` provides a massive speedup (over 100x) for status endpoints. Thread-safe singleton caching with metadata validation and TTL is an effective pattern for frequently read configuration/state files on disk. Using `copy.deepcopy` or `dict.copy` is essential when returning cached objects to prevent accidental mutation of the cache by callers.
**Action:** Always cache expensive system calls and frequently read disk files with appropriate invalidation strategies (TTL + metadata check). Ensure thread safety and use deep copies for non-primitive cached objects.
