## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Dataset Validation and Cleaning]
**Learning:** Pre-compiling regex patterns and using fast-path indicator checks provides significant speedups (~28%) for secret detection on clean datasets. Additionally, `"".join(text.split())` is a more efficient way to remove all whitespace than `re.sub(r"\s+", "", text)`, yielding ~38% speedup in fuzzy hashing.
**Action:** Use pre-compiled regex for repeated matching and prefer built-in string methods over regex for simple character removals in hot paths.
