## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-04 - [Optimized Telemetry Status API with Caching]
**Learning:** Thread-safe caching of status endpoints (get_state, get_gpu_summary, get_last_event_ts) provides significant performance gains (up to 1000x for process-heavy calls like nvidia-smi). Using a TTL-based cache (0.5s-2.0s) with metadata validation (mtime/size) balances responsiveness with data accuracy.
**Action:** Consolidate expensive status-related operations into a centralized telemetry module with a robust caching layer and ensure all monitoring tools (dashboard, HTTP server) use these optimized functions instead of direct I/O or subprocess calls.
