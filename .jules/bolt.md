## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Caching for Status Endpoints]
**Learning:** High-frequency polling of status endpoints (like in TUIs or dashboards) leads to redundant disk IO and expensive subprocess calls. A thread-safe singleton cache using file metadata (mtime/size) and a TTL provides a significant performance boost (~56% faster for state reads) while maintaining data consistency.
**Action:** Implement metadata-validated caching for frequently read configuration/state files and TTL-based caching for expensive system calls (like `nvidia-smi`).
