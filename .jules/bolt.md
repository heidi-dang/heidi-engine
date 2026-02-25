## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-25 - [Telemetry and Status API Caching]
**Learning:** Caching frequently accessed state files (like state.json) using a combination of TTL and file metadata (mtime, size) provides significant performance gains for monitoring tools and status APIs by reducing redundant disk IO and JSON parsing. Caching expensive subprocess outputs (like nvidia-smi) with a TTL is essential for responsive telemetry.
**Action:** Implement thread-safe caching layers for monitoring endpoints and frequently read configuration/state files.
