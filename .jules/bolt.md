## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Efficient Whitespace Removal and Regex Pre-compilation]
**Learning:** Using `"".join(text.split())` is significantly faster (~5x) than `re.sub(r"\s+", "", text)` for removing all whitespace in Python. Additionally, pre-compiling regex patterns at the module level avoids repeated overhead in high-frequency loops.
**Action:** Prefer string methods like `split()` and `join()` for basic text manipulation over regex, and always pre-compile regex patterns used in loops.
