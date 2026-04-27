## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Keyword Fast-path for Secret Detection]
**Learning:** For initial secret detection filtering, Python's 'in' operator for simple keyword matching is significantly faster (approx. 10-12x) than a combined regular expression search.
**Action:** Use keyword-based 'in' checks as a fast-path before triggering expensive regular expression scans for secret detection.
