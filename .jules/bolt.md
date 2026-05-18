## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Validation Pipeline and Telemetry Cache Optimization]
**Learning:** String-based fast-paths for secret detection can provide a ~13x speedup on clean text, but must be carefully implemented to avoid missing high-entropy patterns that lack explicit keywords. Pre-compiling regexes and using faster string methods for whitespace removal also contribute significant gains.
**Action:** Always combine keyword-based fast-paths with independent high-entropy checks to maintain security while optimizing. Ensure module-level caches are correctly implemented without undefined variables.
