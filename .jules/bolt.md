## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Whitespace Removal and Memory Usage in Deduplication]
**Learning:** `"".join(text.split())` is significantly faster than `re.sub(r"\s+", "", text)` for removing all whitespace in Python. Additionally, using generator expressions instead of list comprehensions when passing data to reducers like `Counter` reduces peak memory usage without any performance penalty.
**Action:** Use `split()`/`join()` for bulk whitespace removal and prefer generator expressions for intermediate data processing to improve memory efficiency.
