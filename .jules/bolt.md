## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Whitespace Removal for Fuzzy Hashing]
**Learning:** For stripping all whitespace from a string, Python's `"".join(text.split())` is significantly faster (~5.8x) than `re.sub(r"\s+", "", text)` because it avoids the overhead of the regular expression engine and utilizes optimized string methods.
**Action:** Prefer string methods like `split()` and `join()` over regex for simple character/whitespace manipulations in performance-critical loops.
