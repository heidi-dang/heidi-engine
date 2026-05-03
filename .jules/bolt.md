## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-24 - [Optimized Validation Pipeline]
**Learning:** In Python, stripping all whitespace from a string is significantly faster (approx. 5-7x) using the split/join idiom (`"".join(text.split())`) than using regex (`re.sub(r"\s+", "", text)`). Additionally, a keyword-based fast-path for secret detection can skip expensive regex scans on ~90% of data samples in typical instruction datasets.
**Action:** Prefer split/join for global whitespace removal and always implement keyword fast-paths before complex regex loops in data processing scripts.
