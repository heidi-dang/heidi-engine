## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-25 - [Write-Through Caching for State Management]
**Learning:** In high-frequency polling scenarios (like a dashboard), write-through caching in the state update path () combined with an early-exit cache check in the retrieval path () yields a ~20x performance improvement by eliminating disk I/O and JSON parsing for cache hits.
**Action:** Implement write-through patterns for frequently updated and polled state to minimize system overhead.

## 2026-02-25 - [Write-Through Caching for State Management]
**Learning:** In high-frequency polling scenarios (like a dashboard), write-through caching in the state update path (`save_state`) combined with an early-exit cache check in the retrieval path (`get_state`) yields a ~20x performance improvement by eliminating disk I/O and JSON parsing for cache hits.
**Action:** Implement write-through patterns for frequently updated and polled state to minimize system overhead.
