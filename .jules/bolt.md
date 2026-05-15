## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-15 - [Optimized Validation Pipeline]
**Learning:** For dataset validation scripts, replacing regex-based whitespace removal with `"".join(text.split())` and implementing a string-based keyword fast-path for secret detection provides significant performance gains. String `in` search is ~20x faster than combined regex search for clean lines.
**Action:** Prioritize string-based heuristics over regex for early-exit paths in high-volume data processing.
