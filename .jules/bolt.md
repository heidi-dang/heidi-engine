## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-03-01 - [Validation Pipeline Optimization]
**Learning:** In the dataset validation pipeline,  was a major bottleneck due to redundant regex compilation and scanning of clean text. Also,  is significantly slower than  for whitespace removal in fingerprinting.
**Action:** Implement keyword-based fast-paths for secret detection to skip regex scans on clean data, pre-compile all regex patterns, and use split/join for simple whitespace removal.

## 2026-03-01 - [Validation Pipeline Optimization]
**Learning:** In the dataset validation pipeline, `detect_secrets` was a major bottleneck due to redundant regex compilation and scanning of clean text. Also, `re.sub(r"\s+", "", text)` is significantly slower than `"".join(text.split())` for whitespace removal in fingerprinting.
**Action:** Implement keyword-based fast-paths for secret detection to skip regex scans on clean data, pre-compile all regex patterns, and use split/join for simple whitespace removal.
