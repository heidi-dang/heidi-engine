## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-path Regex Scans and Redundant Cache Bug]
**Learning:** Combined regex fast-paths (using `|` to join multiple patterns) provide a significant speedup (~5x) for scanning safe samples in unit test gates. Additionally, discovered that redundant optimization attempts (like secondary cache checks in `get_state`) can introduce subtle bugs (NameError) if not properly tested or if they reference stale variables.
**Action:** Use combined regex objects for early-exit guards in security/validation scanners. Always verify optimizations with the full test suite to catch regressions in performance-critical paths.
