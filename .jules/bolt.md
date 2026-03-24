## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-24 - [Regex and String Processing Optimizations]
**Learning:** Pre-compiling regex patterns (re.compile) yields a modest performance boost in hot-paths by avoiding internal cache lookups. However, for specific tasks like total whitespace removal, Python's `"".join(text.split())` is significantly faster (~6x) than `re.sub(r"\s+", "", text)`. Additionally, verify that caching layers return the correct data types; a broken cache implementation in `telemetry.py` was found to return string paths instead of dictionary states.
**Action:** Use built-in string methods over regex where possible. Always verify cache return types in unit tests.
