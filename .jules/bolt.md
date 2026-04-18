## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-Path Regex Guards vs "in" Operator]
**Learning:** For a large set of keywords (15+), a single pre-compiled regex fast-path is more efficient and easier to maintain than multiple `in` operator checks. However, ensures the fast-path regex is inclusive enough to avoid false negatives (e.g., matching quotes for high-entropy strings).
**Action:** Use pre-compiled regex for fast-path guards when dealing with many indicators, and always verify that the guard doesn't skip valid matches in the detailed scan.
