## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-01 - [Multi-tier Caching for State and Metadata]
**Learning:** For frequently read files like `state.json`, a multi-tier cache (Fast-path TTL + Slow-path mtime/size validation) provides the best balance of performance and consistency. Subprocess calls like `nvidia-smi` should always be cached with a conservative TTL (e.g., 2s) to prevent blocking the main thread or HTTP event loop.
**Action:** Implement thread-safe caching for core state management to reduce disk I/O and subprocess overhead. Use `copy.deepcopy` to maintain cache isolation.
