## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-01 - [Python Whitespace Removal Optimization]
**Learning:** For stripping ALL whitespace from a string in Python, `"".join(text.split())` is significantly faster (~6.5x in benchmarking) than `re.sub(r"\s+", "", text)` because it avoids the overhead of the regex engine's state machine.
**Action:** Use `split()` and `join()` for simple character or whitespace removal instead of regex whenever possible in performance-critical paths.
