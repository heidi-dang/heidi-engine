## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Thread-Safe Singleton Caching for Status Server]
**Learning:** The `/status` endpoint in a telemetry system can become a major bottleneck if it performs expensive IO (reading state files) or spawns subprocesses (e.g., `nvidia-smi`) on every request. A thread-safe singleton cache with metadata validation (`mtime`, `size`) and TTL provides a significant (90%+) performance boost while maintaining data consistency.
**Action:** Use a `StateCache` singleton to wrap expensive hardware and filesystem queries in multi-threaded environments. Always return deep copies of mutable cached objects to prevent cross-thread corruption.
