## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-24 - [Thread-Safe Telemetry Caching]
**Learning:** Caching `state.json` with metadata validation and TTL provides a significant performance boost for frequently polled status endpoints. Spawning subprocesses like `nvidia-smi` is particularly expensive and should be aggressively cached (2.0s+ TTL). Using `min(500, size)` for backward-seeking in small files prevents `OSError` and is a necessary safety check.
**Action:** Use a thread-safe singleton cache for shared state files to reduce disk IO, and apply TTL-based caching for expensive system calls or file tails.
