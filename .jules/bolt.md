## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-12 - [Restored Telemetry Cache and Optimized Validation]
**Learning:** Removing a buggy cache implementation is a performance regression; it should be fixed instead. Also, regex-based fast-paths for secret detection are safer than string-based keyword lists to maintain "fail-closed" security while improving speed.
**Action:** Fix broken performance optimizations instead of removing them, and use robust fast-path patterns for security-sensitive string processing.
