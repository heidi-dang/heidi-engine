## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-Path Security Regression Risks]
**Learning:** Fast-path keyword checks for secret detection must be strictly case-insensitive or perfectly aligned with the target patterns. Using `any(kw in text_lower)` with uppercase keywords (like "AKIA") in the indicator list causes silent failures. Also, indicators must include punctuation (like quotes) if the regex patterns rely on them for high-entropy string detection.
**Action:** When implementing fast-paths for security-critical logic, verify that the fast-path triggers for ALL target patterns, including those that don't have distinct alphabetic keywords.
