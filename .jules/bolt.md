## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-path String Matching for Secret Detection]
**Learning:** Python's `in` operator for simple keyword matching is significantly faster (approx. 10x) than regular expression searches. However, when using keyword-based fast-paths, the keyword list must be broad enough to catch variants (e.g., using 'api' and 'key' separately to catch 'api-key', 'api_key', and 'apikey').
**Action:** Use broad keyword-based fast-paths before expensive regex scans to improve throughput while maintaining security coverage.
