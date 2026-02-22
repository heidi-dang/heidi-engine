## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [State and Hardware Caching for Status API]
**Learning:** Caching `state.json` with metadata validation (`st_mtime_ns`, `st_size`) and a short TTL (0.5s) effectively reduces redundant disk IO for high-frequency polling. Expensive hardware queries (like `nvidia-smi`) and log seeking should use a longer TTL (1-2s) as they are less likely to change rapidly and have high overhead.
**Action:** Use `StateCache` for state lookups and ensure module-level caching for expensive hardware/IO helpers to optimize monitoring endpoints.
