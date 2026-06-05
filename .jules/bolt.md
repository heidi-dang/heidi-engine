## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-05 - [Fast-path Regex Optimization for Security Scanning]
**Learning:** Security scanning with a large set of regex patterns can be a major bottleneck. A combined regex fast-path (using "any match") can yield significant speedups (e.g., ~5.8x) for safe inputs by skipping individual pattern matching.
**Action:** Use combined regex objects for fast-path checks before iterating over individual patterns in validation or security gates.
