## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Validation Pipeline Optimization]
**Learning:** Combined regex fast-paths (e.g., `_SECRET_INDICATORS.search(text)`) are significantly faster than string-based keyword lists for secret detection when some patterns lack clear keywords (e.g., high-entropy strings). Also, `"".join(text.split())` is ~5x faster than `re.sub(r"\s+", "", text)` for whitespace removal in hot paths like fuzzy hashing.
**Action:** Prefer combined regex for complex fast-path guards to maintain 100% correctness. Use string methods over regex for simple character/whitespace manipulations.
