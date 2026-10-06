## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-08 - [Optimized Whitespace Removal in Fuzzy Hashing]
**Learning:** `"".join(text.split())` is ~6x faster than `re.sub(r"\s+", "", text)` for bulk whitespace removal in Python because `str.split()` operates natively in C without regex engine compilation or matching overhead.
**Action:** Prefer `"".join(text.split())` over regex replacement when stripping all whitespace from strings.
