## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast Whitespace Removal and Broken Cache Fixes]
**Learning:** `"".join(text.split())` is significantly faster (~5x) than `re.sub(r"\s+", "", text)` for removing all whitespace from a string in Python. Also, complex caching logic should always be verified with edge cases (like cache misses) to avoid silent `NameError` or type mismatch regressions.
**Action:** Prefer `split`/`join` over regex for simple global string operations. Ensure all caching layers have explicit unit tests for both hits and misses.
