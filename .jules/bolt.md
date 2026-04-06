## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Multi-run State Caching and Write-Through Updates]
**Learning:** Performance in `heidi_engine/telemetry.py`'s `list_runs` and `get_state` can be significantly regressed if caching only supports a single run or lacks `st_mtime` validation. Implementing a thread-safe multi-run cache with write-through updates and mtime-based invalidation provides ~25x speedup for state retrieval and ~2.4x for listing runs.
**Action:** Use multi-keyed caches with filesystem metadata (`st_mtime`) validation for performance-critical state management that involves frequent polling or multiple concurrent resources.
