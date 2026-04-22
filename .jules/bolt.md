## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-24 - [Fast-Path Regex Synchronization]
**Learning:** Fast-path filters (like `_SECRET_INDICATORS`) must be meticulously synchronized with the complex patterns they guard. In this case, missing the `high_entropy` quote-based pattern in the fast-path would have caused silent false negatives for certain secrets.
**Action:** When implementing fast-path guards, double-check that all guarded patterns are covered by the indicator regex, especially those that rely on structural markers (like quotes) rather than keywords.
