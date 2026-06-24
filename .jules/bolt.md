## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-Path Keyword Scanning vs Regex]
**Learning:** For dataset validation scripts like `scripts/02_validate_clean.py`, simple string keyword scanning (`any(k in text_lower for k in keywords)`) provides a massive speedup (~40x) compared to executing multiple regex searches on clean data. Additionally, `"".join(text.split())` is verified as the fastest way to perform bulk whitespace removal in Python (~4.5x faster than `re.sub`).
**Action:** Prioritize string-based fast-paths before invoking the regex engine for data cleaning tasks, and use split-join for whitespace normalization.
