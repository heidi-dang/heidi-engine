## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Validation Pipeline Optimization]
**Learning:** Pre-compiling regex patterns at the module level and using efficient string methods like '"".join(text.split())' for whitespace removal provides a measurable 2x speedup in data validation pipelines. Avoid redundant dictionary lookups with 'dict.get()' when processing millions of samples.
**Action:** Always pre-compile regex objects and prioritize built-in string/list methods over the regex engine for simple transformations like whitespace removal.
