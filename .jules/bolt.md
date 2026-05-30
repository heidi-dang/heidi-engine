## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-05 - [Optimized Pricing Config Loading and Redaction]
**Learning:** Loading configuration from disk and parsing JSON on every call is a major bottleneck in high-frequency functions. Pre-compiling regexes at the module level provides a significant speedup (up to 2.2x) over string-based .
**Action:** Implement thread-safe caching with a TTL for any function that performs disk I/O but returns relatively static data. Always pre-compile regex patterns that are used repeatedly.

## 2026-03-05 - [Optimized Pricing Config Loading and Redaction]
**Learning:** Loading configuration from disk and parsing JSON on every call is a major bottleneck in high-frequency functions. Pre-compiling regexes at the module level provides a significant speedup (up to 2.2x) over string-based `re.sub`.
**Action:** Implement thread-safe caching with a TTL for any function that performs disk I/O but returns relatively static data. Always pre-compile regex patterns that are used repeatedly.
