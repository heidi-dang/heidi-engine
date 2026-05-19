## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).
## 2026-05-19 - [Validation Pipeline Fast-Path Optimizations]
**Learning:** Combining multiple fields into a single string for a single "fast-path" regex indicator check significantly reduces CPU overhead for expensive multi-pattern scanning (like secret detection) on clean samples. Additionally, using `"".join(text.split())` is measurably faster than `re.sub(r"\s+", "", text)` for bulk whitespace removal.
**Action:** Use fast-path indicator guards for multi-pattern matching and prefer string join/split over regex for simple global replacements in hot loops.
