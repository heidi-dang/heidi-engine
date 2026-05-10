## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-10 - [Keyword-based Fast-Path for Secret Detection]
**Learning:** String 'in' checks are ~70x faster than pre-compiled regex search for identifying the absence of secret markers in clean text. Using a list of lowercase indicators with `any()` on `text.lower()` provides a massive speedup for the common case of non-sensitive data.
**Action:** Always prefer substring checks or keyword-based guards to skip expensive regex processing on the "clean path" of data validation pipelines.
