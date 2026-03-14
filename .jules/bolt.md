## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Run Status API with Write-Through Caching]
**Learning:** In high-frequency polling scenarios (like a TUI dashboard), write-through caching in `save_state` combined with cached `get_state` (0.5s TTL) significantly reduces disk I/O latency. Removing `indent=2` from frequently written JSON state files provides measurable gains in serialization speed (~0.4ms vs ~1.2ms).
**Action:** Implement write-through cache updates for hot state variables and minimize JSON formatting overhead for machine-consumed status files. Always centralize path management to ensure dashboard/telemetry consistency.
