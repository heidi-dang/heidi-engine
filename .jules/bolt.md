## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-05 - [Optimized Validation Fast-Path]
**Learning:** Using a single pre-compiled case-insensitive regex for fast-path indicator checks is more memory-efficient than iterating over a keyword list with `text.lower()`, especially for large payloads, as it avoids unnecessary string duplication.
**Action:** Prefer combined regex search for multi-keyword fast-paths on large strings.
