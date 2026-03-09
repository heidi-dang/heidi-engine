## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Telemetry Caching and Redaction]
**Learning:** Broken caching logic (like redundant checks with undefined variables) can cause silent performance regressions or outright crashes. Pre-compiling regex for hot paths like redaction and implementing mtime-based caching for configuration files provides measurable speedups without sacrificing readability.
**Action:** Always verify that caching logic is correct and handles misses gracefully. Pre-compile regex patterns that are used in tight loops or frequent string processing functions.
