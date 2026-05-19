## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Validation Pipeline Fast-Path Optimization]
**Learning:** In high-volume data validation (like secret scrubbing), sequential regex checks on individual fields are a major bottleneck. A keyword-based fast-path using `any(kw in combined_text_lower for kw in keywords)` provides a ~10x speedup for clean samples by short-circuiting expensive regex scans, provided it's paired with a fallback for non-keyword patterns (like high-entropy strings).
**Action:** Implement combined-text fast-paths with keyword pre-filtering for all multi-pattern validation loops.
