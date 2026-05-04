## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-23 - [Refining Secret Detection Fast-Path]
**Learning:** A simple keyword-based fast-path for secret detection can lead to functional regressions if it misses common markers (like quotes) used by catch-all patterns (like high-entropy strings). While it provides a massive speedup on very clean text, it can slightly de-optimize quoted text that contains no secrets.
**Action:** Always include common markers like quotes in keyword fast-paths for security scanners to ensure comprehensive coverage, and balance the fast-path list to minimize de-optimization on common "safe" patterns.
