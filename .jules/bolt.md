## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Whitespace Removal in Fuzzy Hashing]
**Learning:** For bulk whitespace removal in Python strings, `"".join(text.split())` is significantly faster (~6x) than `re.sub(r"\s+", "", text)` because it avoids the overhead of the regex engine and uses highly optimized C code for splitting and joining.
**Action:** Prefer `"".join(text.split())` over `re.sub` when the goal is to remove all whitespace characters.
