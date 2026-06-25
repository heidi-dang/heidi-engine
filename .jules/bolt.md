## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-25 - [High-Performance Secret Detection and Fuzzy Hashing]
**Learning:** Keyword-based fast-paths for secret detection yield ~7x speedups for clean data. However, fast-paths must be carefully constructed to avoid skipping patterns (like high-entropy strings) that don't rely on keywords. Additionally, `"".join(text.split())` is a significantly more efficient way to perform bulk whitespace removal in Python than regex.
**Action:** Always combine keyword fast-paths with "structural" fast-paths (like checking for quotes) when optimizing search functions to maintain functional parity. Prefer string split-join for global whitespace removal.
