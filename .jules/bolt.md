## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-23 - [Telemetry State and GPU Caching]
**Learning:** Caching frequently read files like `state.json` with `st_mtime_ns` validation provides a 2x speedup for reads. Caching expensive subprocess calls like `nvidia-smi` for 2.0s can provide over 60x speedup for monitoring endpoints. Using `threading.RLock` is essential for re-entrant telemetry calls to avoid deadlocks.
**Action:** Always implement re-entrant locks for core telemetry components and use metadata-based cache validation for local file state.
