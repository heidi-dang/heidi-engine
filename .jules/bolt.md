## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-27 - [Optimized Validation Pipeline and Fixed Telemetry Bug]
**Learning:** For Counter initialization in Python, a list comprehension is slightly faster than a generator expression, despite the memory overhead. Additionally, fast-path regex checks for secret detection must include quote characters to avoid false negatives on high-entropy patterns.
**Action:** Use list comprehensions for Counter when performance is preferred over memory. Ensure fast-path indicators are inclusive of all pattern triggers.
