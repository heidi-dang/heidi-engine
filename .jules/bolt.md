## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-04-21 - [Fast Whitespace Removal in Python]
**Learning:** For removing all whitespace from a string, `"".join(text.split())` is significantly faster (approx. 5-6x) than `re.sub(r"\s+", "", text)` in Python because it uses highly optimized built-in string methods.
**Action:** Prefer `"".join(text.split())` over regex for universal whitespace removal in performance-critical paths.
