## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-path Security Scanning in Unit Test Gate]
**Learning:** Combining multiple regex patterns into a single pre-compiled "fast-path" scan using `|` significantly reduces overhead for safe inputs by converting $O(N \times L)$ scans into a single $O(L)$ scan in the common case.
**Action:** Use a single combined regex for initial detection of any relevant pattern before falling back to individual pattern matching for detailed reporting.
