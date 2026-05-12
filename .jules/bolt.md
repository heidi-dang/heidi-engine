## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2024-05-12 - [Optimized Validation Pipeline]
**Learning:** Keyword-based fast-path checks for secret detection yield ~6.5x speedup for clean text by skipping regex engine overhead. Additionally, "".join(text.split()) is consistently faster than re.sub(r"\s+", "", text) for whitespace removal in Python.
**Action:** Always implement string-based early-exit guards for heavy regex operations in data-intensive loops.
