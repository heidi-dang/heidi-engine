## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-Path Secret Detection and Whitespace Removal]
**Learning:** In the validation pipeline, a combined regex fast-path (`_SECRET_INDICATORS`) for secret detection provides a ~15x speedup for clean samples. For fuzzy hashing, replacing `re.sub(r"\s+", "", text)` with `"".join(text.split())` provides a ~5.5x performance gain.
**Action:** Use combined fast-path indicators to skip expensive sequential scans and prefer `split/join` over regex for simple whitespace removal in performance-critical paths.
