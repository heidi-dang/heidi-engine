## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-31 - [Optimized Validation Pipeline and Fixed Telemetry Cache]
**Learning:** Pre-compiling regex at the module level and using a combined "fast-path" indicator regex significantly improves performance in hot loops (like secret detection) by skipping expensive individual pattern checks for safe data. Additionally, "".join(text.split()) is a measurably faster way to remove all whitespace in Python than re.sub(r"\s+", "", text).
**Action:** Always use pre-compiled regex objects for repeated operations and implement fast-path guards for complex validation logic. Prefer built-in string methods over regex for simple transformations.
