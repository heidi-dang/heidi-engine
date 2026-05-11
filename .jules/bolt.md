## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).
## 2026-05-11 - [Telemetry and Validation Optimization]
**Learning:** String-based fast-paths using `any()` on lowercase text are significantly faster (~10x+) than regex-based fast-paths for checking non-existence of keywords in clean text. Additionally, `"".join(text.split())` is approximately 5x faster than `re.sub(r"\s+", "", text)` for whitespace removal in Python 3.12.
**Action:** Prefer string operations over regex for simple keyword checks and whitespace removal in high-frequency code paths.
