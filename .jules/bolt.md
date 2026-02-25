## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Multi-layered Caching for Telemetry]
**Learning:** High-frequency status polling and event emission can be significantly bottlenecked by redundant disk IO and expensive subprocess calls (like `nvidia-smi`). Implementing a thread-safe cache with metadata validation (`st_mtime_ns`) and short TTLs provides massive speedups (~180x for event timestamps) while maintaining data consistency across processes.
**Action:** For status-heavy modules, implement caching with metadata validation to avoid redundant IO while ensuring correctness when external processes modify state files.
