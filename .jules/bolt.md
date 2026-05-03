## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).
## 2026-05-03 - [Validation Pipeline Optimizations]
**Learning:** Keyword-based fast-paths are highly effective for skipping expensive regex scans in data validation pipelines, provided the keyword list is carefully chosen to avoid common characters (like quotes) that would nullify the fast-path in code-heavy datasets. Additionally, "".join(text.split()) is consistently ~5-7x faster than re.sub(r"\s+", "", text) for global whitespace removal.
**Action:** Prioritize early-exit keyword guards for regex loops and use built-in string methods over regex for simple character removals.
