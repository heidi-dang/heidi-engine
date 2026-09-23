## 2026-02-21 - [Fast Bulk Whitespace Removal in String Processing]
**Learning:** For stripping all whitespace from text in high-frequency string operations (e.g., fuzzy fingerprinting during dataset deduplication), `"".join(text.split())` is ~5.2x faster than `re.sub(r"\s+", "", text)` as C-optimized string splitting completely bypasses regex engine overhead.
**Action:** Use `"".join(text.split())` instead of regex `re.sub(r"\s+", "", text)` when stripping whitespace from strings.

## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).
