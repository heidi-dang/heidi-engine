## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Validation Pipeline Performance Tuning]
**Learning:** Pre-compiling regular expressions at the module level avoids redundant compilation overhead in loops. For whitespace removal, `"".join(text.split())` is significantly more efficient than `re.sub(r"\s+", "", text)` in Python. High-frequency polling functions (like telemetry state reads) benefit greatly from thread-safe caching to avoid disk I/O bottlenecks.
**Action:** Use module-level compiled regex objects for hot paths and prefer native string methods over regex for simple whitespace operations. Ensure cache lookups use correct keys to avoid `NameError` or redundant misses.
