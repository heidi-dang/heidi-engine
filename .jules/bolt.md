## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-16 - [Robust Fast-Path Regex Guards]
**Learning:** Fast-path regex guards for complex scanners (like secret detectors) must be carefully designed to cover ALL patterns, including those that don't rely on specific keywords (like high-entropy strings). A flawed fast-path can lead to silent functional regressions.
**Action:** When implementing fast-paths, ensure they include delimiters (like quotes or brackets) or other structural indicators that could trigger any of the underlying patterns, even if they don't match a specific keyword.
