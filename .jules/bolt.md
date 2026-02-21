## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [State Caching and GPU Monitoring Optimization]
**Learning:** Frequent disk I/O for small state files and repeated subprocess calls (like `nvidia-smi`) are major overheads for real-time monitoring. Implementing a thread-safe singleton cache with metadata validation (mtime/size) and a short TTL provides significant speedups (~7x) with minimal risk of staleness.
**Action:** Use `StateCache` for frequently read metadata and apply short-lived caching to expensive hardware polling operations.
