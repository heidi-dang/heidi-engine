## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-22 - [Optimized Regex Scanning in Unit Test Gate]
**Learning:** Combining multiple independent regex patterns into a single pre-compiled "fast-path" regex using the "|" operator significantly reduces scanning passes and improves performance by ~5.1x for samples that do not match any patterns.
**Action:** Use combined pre-compiled regexes for security scans and keyword detection heuristics to minimize overhead in high-throughput scripts.
