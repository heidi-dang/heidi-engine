## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Dataset Cleaning Performance]
**Learning:** For fuzzy hashing, `"".join(text.split())` is significantly faster (~40% on large strings) than `re.sub(r"\s+", "", text)` for whitespace removal. In secret detection, a single-pass combined regex check on joined fields serves as an efficient fast-path for clean data.
**Action:** Prefer string methods over regex for simple character/whitespace operations in hot loops. Use combined regex fast-paths to avoid iterative scanning of multiple patterns on clean inputs.
