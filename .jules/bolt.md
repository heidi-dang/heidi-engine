## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Telemetry Caching and Write-Through Optimization]
**Learning:** Implementing a write-through cache for frequently accessed state (like telemetry `state.json`) prevents redundant disk I/O during high-frequency operations like `emit_event`. For configuration files that rarely exist (like `pricing.json`), caching the "negative" result (file not found) with a small TTL is crucial to avoid repeated `os.path.exists` syscalls.
**Action:** Always ensure that read-side cache lookups are correctly preserved when refactoring caching logic, and use `copy.deepcopy` to prevent accidental mutation of global defaults or cached objects. Use `time.monotonic()` for robust TTL checks.
