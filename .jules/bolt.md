## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).
## 2026-02-26 - [Multi-layered Telemetry Caching]
**Learning:** Caching frequently accessed pipeline state (state.json) and external command outputs (nvidia-smi) yields significant performance gains. get_state improved from ~0.09ms to ~0.01ms (8.4x speedup) by using a thread-safe StateCache with TTL and metadata validation.
**Action:** Always implement caching for frequently polled status endpoints and expensive system metrics to reduce disk IO and subprocess overhead.
