## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-04 - [Combined Regex Regression in Validation]
**Learning:** In the dataset validation pipeline, implementing a combined regex (using '|' alternation) for secret detection across multiple fields resulted in a ~1.5x performance regression compared to individual pre-compiled regex checks. This is likely due to the overhead of the combined DFA/NFA state machine on safe inputs.
**Action:** Avoid combined regex "fast-paths" for large, complex pattern sets without exhaustive benchmarking across both 'clean' and 'dirty' data distributions. Stick to individual pre-compiled regex objects for multi-field scanning.
