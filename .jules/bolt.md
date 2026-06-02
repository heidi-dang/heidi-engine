## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-20 - [Validation Pipeline Optimization]
**Learning:** Pre-compiling regular expressions at the module level is a high-impact, low-complexity optimization for scripts that process data in loops. Additionally, `"".join(text.split())` is significantly faster (~4x) than `re.sub(r"\s+", "", text)` for whitespace removal in Python.
**Action:** Use `split()` and `join()` for simple whitespace normalization and pre-compile all regexes used within data processing loops.
