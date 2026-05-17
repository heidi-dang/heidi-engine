## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).
## 2026-02-21 - [Validation Pipeline Optimization]
**Learning:** Combining multiple regex patterns into a single "indicator" regex for a fast-path search provides significant speedups (~29%) for "clean" data by avoiding the overhead of iterating through a long list of specific regex patterns. Additionally, using string split/join for whitespace removal is measurably faster (~25%) than `re.sub` in Python.
**Action:** Use compiled fast-path regexes for filter-heavy loops and prefer built-in string methods over regex for simple character-set operations like whitespace removal.
