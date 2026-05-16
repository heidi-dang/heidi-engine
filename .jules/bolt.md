## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-23 - [Thread-Safe TTL Caching for Config Lookups]
**Learning:** High-frequency paths that depend on disk-based configuration (like pricing lookups during event emission) benefit significantly (~150x) from thread-safe TTL caching. However, redundant cache checks that mimic existing patterns but use undefined variables (e.g., in get_state) lead to NameError regressions.
**Action:** Use threading.Lock and time.monotonic() for robust TTL caching. When cleaning up redundant code, explicitly verify that primary optimizations remain functional and all variables are defined.
