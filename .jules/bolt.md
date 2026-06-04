## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Validation Pipeline Optimizations]
**Learning:** Pre-compiling regex objects at the module level and using a combined "fast-path" regex for initial filtering can yield significant speedups (up to 6x) for safe samples in security/validation checks. Native string methods like "".join(text.split()) are much faster than re.sub for simple whitespace removal.
**Action:** Use pre-compiled regex fast-paths for filtering and prioritize native string methods over regex for simple transformations. Always ensure case-sensitivity is handled correctly when combining regex patterns.
