## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-22 - [Optimized Validation Hot-Path in 02_validate_clean.py]
**Learning:** Whitespace removal in Python is significantly faster using `"".join(text.split())` than `re.sub(r"\s+", "", text)` (approx. 18x speedup). Additionally, pre-compiling regex patterns outside of loops and using a fast-path keyword check to skip expensive searches on clean samples can provide measurable gains even for small datasets.
**Action:** Use string split-join for basic whitespace removal. Pre-compile regex and implement early-exit guards for expensive validation logic that must process every sample in a dataset.
