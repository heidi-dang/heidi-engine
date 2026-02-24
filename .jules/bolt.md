## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-05 - [Optimized Status API with State and Subprocess Caching]
**Learning:** Caching frequently polled data like `state.json` and hardware metrics (via `nvidia-smi`) drastically reduces I/O and subprocess overhead. Using metadata validation (`st_mtime_ns`, `st_size`) allows for safe, cross-process caching with minimal overhead compared to full JSON parsing.
**Action:** For frequently polled endpoints or functions, implement TTL-based caching and use lightweight metadata checks to validate cache freshness before falling back to expensive I/O or subprocess calls.
