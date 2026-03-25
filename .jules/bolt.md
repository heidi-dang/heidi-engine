## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Heuristic Fast-path Correctness]
**Learning:** Combining multiple complex regex patterns into a single "fast-path" indicator can lead to functional regressions if the indicator list is not kept perfectly in sync with the granular patterns. Furthermore, the performance gain of a combined regex can be negated by engine overhead on very long strings compared to pre-compiled individual patterns.
**Action:** When implementing fast-path guards, verify coverage against the full pattern set using automated correctness tests. For very long strings, prioritize individual `pattern.search()` over a massive combined regex if the combined regex becomes a bottleneck.
