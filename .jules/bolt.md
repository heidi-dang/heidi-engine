## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-18 - [Combined Regex vs Sequential Search]
**Learning:** Combining multiple complex regex patterns into a single alternation (p1|p2|...) for a fast-path check was surprisingly slower (~1.4x) than running sequential `re.search` calls with pre-compiled objects on safe text. This is likely due to the overhead of the backtracking engine when handling many complex sub-patterns in a single pass.
**Action:** Prefer sequential searches with pre-compiled regex objects for sets of complex patterns, or use a very simple, non-capturing keyword-based fast-path if necessary.
